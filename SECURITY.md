# Security Policy

We take the security of Zienswijzer seriously. Thank you for helping keep the
project and its users safe.

## Supported versions

Security fixes are applied to the latest released version on the `main` branch.
We recommend always running the most recent release.

| Version | Supported          |
| ------- | ------------------ |
| `main` (latest) | :white_check_mark: |
| older releases  | :x:                |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Instead, report them privately by either:

- Using GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
  ("Report a vulnerability" under the repository's **Security** tab), or
- Emailing **lex@gradient-ds.com**.

Please include as much detail as possible:

- A description of the vulnerability and its impact.
- Steps to reproduce (proof-of-concept, affected endpoints/components).
- The affected version, commit, or image tag.
- Any suggested remediation, if you have one.

## What to expect

- **Acknowledgement** of your report within **5 business days**.
- An assessment and, where confirmed, a remediation plan with an indicative
  timeline.
- Coordinated disclosure: we ask that you give us a reasonable window to release
  a fix before any public disclosure. We are happy to credit you once the issue
  is resolved, unless you prefer to remain anonymous.

## Our security practices

- Container images are scanned for known vulnerabilities with
  [Trivy](https://github.com/aquasecurity/trivy) (`./scripts/trivy-scan.sh`).
  Builds are expected to be free of HIGH/CRITICAL (CVSS ≥ 7.0) findings.
- Python dependencies are pinned via `backend/uv.lock` for reproducible,
  auditable builds.
- Secrets (e.g. OAuth credentials) are provided at runtime via the environment
  and are never baked into container images.
