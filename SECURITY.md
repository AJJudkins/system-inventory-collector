# Security policy

## Scope and safety
local-only and read-only: no network connections, hostname excluded unless `--include-hostname`, `--no-packages` to omit software lists, output files are `0600` and never overwritten without `--force`.

## What was and was not tested
**Tested (automated, in CI and locally):** collection, JSON/CSV output and file-safety behavior on Linux (containers and CI).

**Not tested:** Windows and macOS, systems without psutil in unusual environments, and any large fleet use; it inventories only the machine it runs on.

## Reporting a problem
This is a small personal portfolio project, not a supported product. If you find a security issue, please open a GitHub issue **without** secrets, credentials or real system details, or use GitHub's "Report a vulnerability" button on the Security tab if it is enabled.
