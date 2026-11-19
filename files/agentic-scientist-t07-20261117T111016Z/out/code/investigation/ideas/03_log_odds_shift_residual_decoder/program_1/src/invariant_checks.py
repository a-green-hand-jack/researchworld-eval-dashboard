"""Runtime checks for the common nested design and anonymous histories."""

import numpy as np


def check_selection(selection_order, item_groups, budget, previous_items):
    query_items = selection_order[:budget]
    assert query_items.size == budget
    assert np.unique(item_groups[query_items]).size == budget
    assert np.array_equal(query_items[:len(previous_items)], previous_items)


def check_predictions(observed, predictions):
    assert predictions.shape == (observed.shape[0],)
    assert np.all(np.isfinite(predictions))
    assert np.all((predictions >= 0) & (predictions <= 1))
    if observed.shape[0] == 0:
        return
    histories = {}
    for answers, prediction in zip(observed, predictions):
        history = answers.tobytes()
        if history in histories:
            assert prediction == histories[history]
        else:
            histories[history] = prediction
