# Setup attempts (2026-11-03)

- llama-cpp-python CPU wheel 0.3.2 installed successfully, but import failed: `libc.musl-x86_64.so.1: cannot open shared object file`.
- CPU wheel 0.3.18 also installed, but import failed with the same missing musl C library. Neither wheel produced any responses or results.
- Initial conda-forge compiler installation failed TLS certificate verification (`unable to get local issuer certificate`). Retrying with the system certificate bundle explicitly configured, without disabling verification.
- Initial urllib retrieval of Qwen2.5-1.5B Q4_K_M stopped after 930217984 of 1117320736 bytes (`ContentTooShortError`). Resuming with curl; this incomplete file has not been used for inference.

No forbidden literature or associated material has been sought or read. Network accesses so far were exact package/model/data locations only.
- Explicitly selecting `/etc/ssl/certs/ca-certificates.crt` also failed conda TLS verification. Explicitly selecting Python's configured `/run/hutian/ca-bundle.pem` succeeded; compiler/CMake installed from conda-forge with verification on.
- The interrupted 1.5B model download resumed successfully to the expected 1117320736 bytes; complete SHA-256 is in `downloads.json`.

## Native-backend pilot anomaly and units

The representative validation pilot succeeded. One completion reported 9 usage tokens despite the `max_tokens=8` request: question45/candidate15, a length-ending malformed response containing a multibyte logical symbol. The exact raw output and reported usage remain in `results/real-pilot-scope.jsonl`; actual token totals always use recorded backend usage, not the requested cap. This observation does not justify rewriting main responses or changing the frozen parser. Further backend-source explanation is recorded separately if established.

On this Linux environment, Python `resource.getrusage(...).ru_maxrss` is in KiB. Earlier output schema names the field `maxrss_kb` and some notes abbreviate it KB; interpret those measurements as KiB. The representative value3372800 is3293.75MiB or approximately3.217GiB, below the4096MiB memory ceiling. Preserve the original measurement value rather than silently changing it.

The source of the native Python backend explains how the requested token cap can be exceeded: its multibyte UTF-8 fix executes `continue` before the later `len(completion_tokens) >= max_tokens` check. Finishing an incomplete UTF-8 sequence can therefore extend the reported token count. This is an implementation behavior, not a fabricated measurement or silently discarded output; source reading scope/hash are in `native-token-limit.json`. The protocol reports the argument as **requested max_tokens8** and all accounting uses actual reported usage.
