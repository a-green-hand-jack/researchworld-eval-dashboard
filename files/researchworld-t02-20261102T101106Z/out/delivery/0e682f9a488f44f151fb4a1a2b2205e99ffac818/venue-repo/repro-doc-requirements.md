# Reproduction document: required contents (objective `deliverable.md`, item 2)

The owner is `paper-repo` (assembles) with `experiment-repo` (code, commands, timings) and `figtab-repo` (figure/table scripts).
Each item below must be present and verifiable; mark anything not done as not done.

1. **Environment**: Python and package versions (from `ht-role environment --lock` / `pip freeze`), OS, CPU model and cores, memory, no GPU (or GPU stated).
2. **Data**: synthetic modular-arithmetic data, constructed in memory; state the operation(s), prime(s) `p`, the enumeration of all p^2 pairs, the label
   function, the train/validation split rule and fraction, the split seed. "No download, no account, no license, no version to pin" (data.md).
   Any extra synthetic data: construction in the paper.
3. **Seeds**: seed list per experiment and what each seed controls (init, split, data order).
4. **Commands**: exact command per experiment and its expected wall-clock on the stated hardware (measured values, with the machine).
5. **Artifact map**: table "Table/Figure N -> script -> input results file(s) -> command", covering every table and figure in the paper and appendix.
6. **Results provenance**: which commit of the code produced the results files used in the paper; results files kept in the repository.
7. **Withheld-paper exposure**: see `venue.md` section 5; either "none encountered" or the record (what, where, how much was read).
8. **Unfinished/failed runs**: list of runs planned but not completed, or failed, and where they appear in the paper.
9. **LLM/agent assistance** statement if applicable (NeurIPS asks only for important/non-standard use; state it anyway for provenance).
10. **Template/build**: `latexmk -pdf <main>.tex`, the NeurIPS 2026 template version (`venue-repo/template/SOURCE.md`), main-text page count of the built PDF.
