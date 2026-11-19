# Leaderboard stability: context supply

This repository owns the objective/context function, not final experiments or manuscript layout. The full requirement brief is [context/brief.md](context/brief.md) and the wiki `Brief` page.

Usable handoff:

- [Prior work and contribution boundaries](context/prior_work.md): source-specific claims, deletion/injection/reversal distinctions and citation limits.
- [Method and display conventions](context/method_conventions.md): conditional estimand, loss normalization, influence replacement derivation, comparison units and uncertainty objects.
- [Reviewed bibliography](context/reviewed_sources.bib): seven actual consulted papers; original Bradley–Terry article is excluded because only metadata was accessible.
- [Reading/access record](context/reading_log.md) and [source provenance](context/sources.json): inspected sections, versions, hashes and exact access failures.
- [Explicit-source downloader](context/fetch_sources.py): `python3 context/fetch_sources.py --output /path/outside/repository/reading`. Python standard library only. Cached matching PDFs are verified without network use. Raw papers/data are not bundled.

The `Brief`, `Prior-Work`, `Method-Conventions` and `Reading-Log` wiki pages and a context release expose the material to positions with release/wiki access. Story-repo owns the split; paper-repo integrates source notes and bibliography into its owned report. No final context path is requested in paper-repo. The existing analysis release informs reporting constraints but its numerical results are owned and validated by experiment-repo.
