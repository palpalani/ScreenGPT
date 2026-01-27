# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing the maintainers directly. Do not open a public issue.

We will acknowledge receipt within 48 hours and provide a detailed response within 7 days.

## Known Vulnerabilities

### protobuf <= 6.33.4 (Transitive Dependency)

**Status:** Unpatched (no fix available)
**Severity:** Medium
**CVE:** Pending

**Description:** A denial-of-service (DoS) vulnerability exists in `google.protobuf.json_format.ParseDict()` where the `max_recursion_depth` limit can be bypassed when parsing nested `google.protobuf.Any` messages.

**Impact on ScreenGPT:** Low. This package is a transitive dependency of Streamlit (UI). ScreenGPT does not directly use `protobuf.json_format.ParseDict()` with untrusted input.

**Mitigation:**
- The vulnerability requires an attacker to supply deeply nested protobuf Any structures
- ScreenGPT's API accepts PDF files, not protobuf messages
- Monitor for upstream fix in protobuf > 6.33.4

**Action:** Will update when a patched version becomes available.
