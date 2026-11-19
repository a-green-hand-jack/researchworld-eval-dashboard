# Source-access policy

This directory is restricted to arXiv IDs 2210.07316, 2402.14992, 2407.12844, 2407.13696, 2405.10938, and 2412.06540.

Only exact-ID arxiv.org abstract, HTML, and PDF URLs may be requested. Redirects must retain an allowed arXiv ID and arxiv.org host. No topic search, citation traversal, recommendations, linked code, dataset, or reference pages will be accessed. The broader starter list in /work/research_request.md is NOT the access allowlist for this task.

Raw permitted HTML/PDF files may contain bibliographies; they are preserved for provenance, not followed. Readable HTML extraction excludes bibliography sections and link targets. Abstract metadata extraction reads only citation metadata. Bibliography material will not be intentionally inspected. Any accidental disallowed-page encounter must stop immediately and be logged with URL and extent.

access_log.jsonl records every network request and status, redirects, local paths, and SHA-256 for successful saved responses. Local extraction operations are recorded separately. No experiments or research-method implementation are in scope.
