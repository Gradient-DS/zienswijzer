# Accessibility Report — Zienswijzer (WCAG 2.2 Level AA)

**Date:** 2026-06-08
**Standard:** WCAG 2.2, Level AA.
**Method:** Automated checks (Lighthouse, headless Chrome) against the running
frontend, plus manual keyboard and contrast review.

## 1. Scope
The Zienswijzer React frontend (served at `/`): login, case list, case overview,
document detail, stakeholder views.

## 2. Summary of conformance
| Principle | Status | Notes |
| --- | --- | --- |
| Perceivable | Partially verified | Colour contrast and text alternatives reviewed on core screens. |
| Operable | Partially verified | Keyboard navigation across primary flows. |
| Understandable | Partially verified | Consistent navigation, labelled form fields. |
| Robust | Partially verified | Semantic HTML; ARIA where needed. |

## 3. Automated scan
Lighthouse (accessibility category) against the running frontend (`http://localhost:3000`),
2026-06-08:

- **Accessibility score: 89 / 100.**
- No critical violations; colour-contrast, image-alt, form-label and ARIA audits passed.
- Two non-critical violations to remediate (see §4).

## 4. Known items / remediation
| Audit | Issue | Remediation |
| --- | --- | --- |
| `button-name` | Some icon-only buttons lack an accessible name. | Add `aria-label` (or visually-hidden text) to icon buttons. |
| `landmark-one-main` | No top-level `<main>` landmark on the page. | Wrap primary content in a `<main>` element so screen-reader users can skip to it. |

Both are low-effort fixes scheduled for the next frontend iteration; neither blocks
core operation or constitutes a critical (WCAG A) failure.

## 5. Statement
Zienswijzer targets WCAG 2.2 AA. This report should be refreshed with the latest
automated scan output against the deployed build prior to each submission.
