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

- **Accessibility score: 100 / 100. No violations.**
- Colour-contrast, image-alt, form-label, ARIA, and landmark audits all pass.

## 4. Remediated items
The initial scan (89/100) surfaced two non-critical issues, both fixed in this release:

| Audit | Issue | Fix |
| --- | --- | --- |
| `button-name` | Icon-only navigation buttons lacked an accessible name. | Added `aria-label` to the menu/sidebar toggle buttons (`pages/HomePage.tsx`). |
| `landmark-one-main` | No top-level `<main>` landmark. | Wrapped the primary content (`<Outlet/>`) in a `<main>` element. |

Re-scan after the fixes: **100/100, no remaining violations.**

## 5. Statement
Zienswijzer targets WCAG 2.2 AA. This report should be refreshed with the latest
automated scan output against the deployed build prior to each submission.
