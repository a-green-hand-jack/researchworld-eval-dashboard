# Research task: Confidence-interval width when the labeled set, the unlabeled set and the predictor are all fixed

## Problem and motivation

In many scientific fields (ecological remote sensing, astronomical morphology classification, census analysis, etc.), analysts are often in the following setting:

- only a small sample with gold-standard labels (costly to obtain, and the main bottleneck of precision);
- a large sample with features only and no labels;
- an already pre-trained, non-modifiable prediction model that can give a predicted value for any sample.

The goal is to construct a **statistically valid confidence interval** for some population parameter of interest (the specific estimation target is chosen by you and justified): the nominal coverage must hold, and at the same time the interval should be as narrow as possible.

In recent years there are methods that combine predictor outputs with labeled data for valid inference. This task fixes the constraints further: no additional labels, no change of predictor, no additional unlabeled samples.

**Core question: with the labeled set, the unlabeled set and the predictor all fixed, and the nominal coverage required to hold, can the confidence intervals given by existing methods be shortened further? By how much? Under what conditions can they, and under what conditions can they not?**

## Requirements

Please, as an independent researcher:

1. review how existing methods work in this setting and what they assume, and make explicit the specific research question you will answer;
2. propose and test your route, comparing it with the existing valid-interval methods that are available; you may use public real datasets, and may supplement them with synthetic data with known ground truth;
3. report the evidence and the limitations, and state under what conditions the conclusion brings a gain and under what conditions it does not; if you can give a theoretical analysis, state the assumptions and the scope of applicability, and check it with experiments.

## How success is measured

- Validity: under repeated sampling, the empirical coverage of the interval reaches the nominal level (for example 95%);
- Width: a comparison of the average interval width given the same inputs;
- The conclusions must be supported by repeated experiments and an uncertainty report.

The conclusion may be support, refutation or conditional; results of no gain or of invalid intervals are equally accepted.

## Constraint summary

CPU only, time limit one week, no paid API needed (see `resources.md` for details); the data can be public real data or synthetic data you generate yourself (see `data.md` for details); the output is a paper plus code (see `deliverable.md` for details).

Take the research question and the experimental evidence as the main thread, and decide the specific route yourself.
