# Re-review of the final version (paper-repo PR 17, head aa11838c8d0c)

Built document: `main/document.pdf` on the `document` branch, `built-from` = aa11838c8d0c, 23 pages (9 main pages, references, checklist, appendix).

## Answers to the `must` findings of b2c5ebe

- **F1 (contact statement).** `README.md` now has "Contact with the withheld paper", with a statement from each role that searched or read (idea, experiment, venue, paper), what was queried and read, and what each cannot exclude. It is in the README rather than `code/REPRODUCE.md`; the README is the top-level reproduction entry and is where a reader meets it. Answered.
- **F2 (R3 verdict).** §3 now states the rule (refuted for a rule only if held-out R² >= 0.9 in every direction; supported if it fails in at least one), §6.4 applies it ("borne out for all seven rules, since each fails in its worst direction") and says the gap carries the minimum's and median's price in single directions only, Table 3's heading states the worst-of-six rule, and the abstract says the relation "fails to transfer between boards in at least one direction for every rule". Numbers are unchanged. Answered. The rule is a reading of the Brief's R3 criterion, which does not say which direction decides; it is now explicit and consistent, and the best-direction values are reported beside it.

## Rest of the diff against 05011da

Wording trims to keep nine pages (limitations, R5 sentence). No results, figures or claims change.

## Open `may` items (not blocking)

m1-m6, m8 as in `version1-pr13.md`.

## Conclusion

Approved at aa11838c8d0c as the final version: no `must` finding remains, the paper meets the objective and the NeurIPS 2026 format.
