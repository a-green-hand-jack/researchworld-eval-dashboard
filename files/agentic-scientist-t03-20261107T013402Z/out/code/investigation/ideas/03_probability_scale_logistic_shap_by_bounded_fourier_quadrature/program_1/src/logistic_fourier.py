"""Bounded probability-game Fourier/Owen integration; failure returns None.

Mesh agreement and endpoint efficiency are numerical diagnostics, not rigorous
coordinate-error certificates. No coalition predictions or random draws occur.
"""

import math

import numpy as np


def _frequency_marginals(frequencies, base_logit, increments,
                         inclusion_nodes, inclusion_weights):
    phase_steps = np.exp(1j * frequencies[:, None] * increments[None, :])
    mixture_factors = 1.0 - inclusion_nodes[None, :, None] + inclusion_nodes[None, :, None] * phase_steps[:, None, :]
    ones = np.ones((*mixture_factors.shape[:2], 1), dtype=np.complex128)
    prefix = np.concatenate((ones, np.cumprod(mixture_factors, axis=2)), axis=2)
    suffix = np.concatenate((np.cumprod(mixture_factors[:, :, ::-1], axis=2)[:, :, ::-1], ones), axis=2)
    excluded_products = prefix[:, :, :-1] * suffix[:, :, 1:]
    t_integrals = np.einsum('q,fqj->fj', inclusion_weights, excluded_products)
    complex_marginals = np.exp(1j * frequencies[:, None] * base_logit) * np.expm1(1j * frequencies[:, None] * increments[None, :]) * t_integrals
    return np.imag(complex_marginals) / np.sinh(np.pi * frequencies[:, None])


def _frequency_mesh(base_logit, increments, inclusion_nodes, inclusion_weights,
                    cutoff, panel_count, frequency_nodes, frequency_weights):
    frequency_block_size = 32
    panels_per_block = frequency_block_size // len(frequency_nodes)
    panel_width = cutoff / panel_count
    estimate = np.zeros(len(increments), dtype=np.float64)
    for panel_start in range(0, panel_count, panels_per_block):
        panel_indices = np.arange(panel_start, min(panel_count, panel_start + panels_per_block))
        frequencies = (panel_width * (panel_indices[:, None] + 0.5 * (frequency_nodes + 1.0))).reshape(-1)
        weights = np.tile(0.5 * panel_width * frequency_weights, len(panel_indices))
        marginals = _frequency_marginals(frequencies, base_logit, increments,
                                        inclusion_nodes, inclusion_weights)
        if not np.all(np.isfinite(marginals)):
            return None
        estimate += weights @ marginals
    return estimate


def _integrate_row(base_logit, increments, endpoint_difference,
                   inclusion_nodes, inclusion_weights, frequency_nodes,
                   frequency_weights):
    cutoff = 8.0
    tail_tolerance = 1e-10
    quadrature_tolerance = 1e-8
    efficiency_tolerance = 1e-8
    maximum_frequency_nodes = 2048
    tail_bound = -(2.0 / np.pi) * np.log(np.tanh(np.pi * cutoff / 2.0))
    minimum_logit = base_logit + np.minimum(increments, 0.0).sum()
    maximum_logit = base_logit + np.maximum(increments, 0.0).sum()
    maximum_phase = max(abs(minimum_logit), abs(maximum_logit))
    if not math.isfinite(maximum_phase):
        return None
    initial_panel_limit = maximum_frequency_nodes // (4 * len(frequency_nodes))
    if maximum_phase > initial_panel_limit * (8.0 / cutoff):
        return None
    panel_count = max(1, math.ceil(cutoff * maximum_phase / 8.0))
    required_frequency_nodes = 4 * panel_count * len(frequency_nodes)
    if required_frequency_nodes > maximum_frequency_nodes:
        return None
    if tail_bound > tail_tolerance or not math.isfinite(endpoint_difference):
        return None
    coarse_phi = _frequency_mesh(base_logit, increments, inclusion_nodes,
                                 inclusion_weights, cutoff, panel_count,
                                 frequency_nodes, frequency_weights)
    if coarse_phi is None or not np.all(np.isfinite(coarse_phi)):
        return None
    consecutive_agreements = 0
    while True:
        panel_count *= 2
        required_frequency_nodes = panel_count * len(frequency_nodes)
        if required_frequency_nodes > maximum_frequency_nodes:
            return None
        refined_phi = _frequency_mesh(base_logit, increments, inclusion_nodes,
                                      inclusion_weights, cutoff, panel_count,
                                      frequency_nodes, frequency_weights)
        if refined_phi is None:
            return None
        if not np.all(np.isfinite(refined_phi)):
            return None
        discretization_error = np.max(np.abs(refined_phi - coarse_phi))
        efficiency_error = abs(refined_phi.sum() - endpoint_difference)
        if tail_bound <= tail_tolerance and discretization_error <= quadrature_tolerance and efficiency_error <= efficiency_tolerance:
            consecutive_agreements += 1
            if consecutive_agreements >= 2:
                return refined_phi
        else:
            consecutive_agreements = 0
        coarse_phi = refined_phi


def _logistic_fourier_shapley(model, query):
    coefficients = np.asarray(model['parameters']['coef'], dtype=np.float64)
    intercept = float(model['parameters']['intercept'])
    query_values = np.asarray(query, dtype=np.float64)
    background = np.asarray(model['background'], dtype=np.float64)
    feature_count = model['dimension']
    if not (np.all(np.isfinite(coefficients)) and math.isfinite(intercept)):
        return None
    raw_nodes, raw_weights = np.polynomial.legendre.leggauss((feature_count + 1) // 2)
    inclusion_nodes = 0.5 * (raw_nodes + 1.0)
    inclusion_weights = 0.5 * raw_weights
    frequency_nodes, frequency_weights = np.polynomial.legendre.leggauss(8)
    query_logit = float(query_values @ coefficients + intercept)
    if not math.isfinite(query_logit):
        return None
    query_probability = 1.0 / (1.0 + np.exp(-np.clip(query_logit, -700, 700)))
    background_phi = np.empty((len(background), feature_count), dtype=np.float64)
    for row_index, background_row in enumerate(background):
        increments = coefficients * (query_values - background_row)
        base_logit = float(background_row @ coefficients + intercept)
        if not math.isfinite(base_logit) or not np.all(np.isfinite(increments)):
            return None
        base_probability = 1.0 / (1.0 + np.exp(-np.clip(base_logit, -700, 700)))
        endpoint_difference = float(query_probability - base_probability)
        row_phi = _integrate_row(base_logit, increments, endpoint_difference,
                                 inclusion_nodes, inclusion_weights,
                                 frequency_nodes, frequency_weights)
        if row_phi is None:
            return None
        background_phi[row_index] = row_phi
    return background_phi.mean(axis=0)


def logistic_fourier_shapley(model, query):
    """Average every supplied row, or reject without consuming sampling RNG.

    Sigmoid(z) = 1/2 + integral sin(omega*z)/sinh(pi*omega) d omega.
    The integrand's zero-frequency limit is increments/pi. Interior frequency
    nodes and expm1 avoid subtracting nearly equal complex phases. Clipping at
    magnitude 700 perturbs sigmoid below ordinary float64 absolute precision.
    """
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise', under='ignore'):
            return _logistic_fourier_shapley(model, query)
    except (FloatingPointError, OverflowError):
        return None
