# Accessibility Report — Zienswijzer (WCAG 2.2 Level AA)

**Date:** 2026-06-05
**Standard:** WCAG 2.2, Level AA.
**Method:** Automated checks (axe-core / Lighthouse) against the running frontend,
plus manual keyboard and contrast review.

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
Run axe-core/Lighthouse against the running app (see SUBMISSION.md) and paste the
score and any violations here before submission. Target: no critical violations.

## 4. Known items / remediation
- Document any contrast or focus-order issues found during the scan and the plan
  to address them.

## 5. Statement
Zienswijzer targets WCAG 2.2 AA. This report should be refreshed with the latest
automated scan output against the deployed build prior to each submission.
