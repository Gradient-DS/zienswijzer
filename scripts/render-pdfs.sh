#!/usr/bin/env bash
set -euo pipefail
# Render audit markdown -> PDF. Tries pandoc direct; if pandoc has no PDF engine,
# falls through to pandoc->HTML + weasyprint; else headless Chrome.
render() {
  local md="$1" pdf="${1%.md}.pdf"
  if command -v pandoc >/dev/null; then
    pandoc "$md" -o "$pdf" && { echo "pandoc -> $pdf"; return; }
  fi
  if command -v weasyprint >/dev/null && command -v pandoc >/dev/null; then
    pandoc "$md" -o /tmp/_a.html && weasyprint /tmp/_a.html "$pdf" && { echo "weasyprint -> $pdf"; return; }
  fi
  # Headless Chrome fallback (markdown rendered as preformatted HTML).
  python3 -c 'import html,sys; print("<pre>"+html.escape(open(sys.argv[1]).read())+"</pre>")' "$md" > /tmp/_a.html
  for chrome in "google-chrome" "chromium" "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
    if command -v "$chrome" >/dev/null 2>&1 || [ -x "$chrome" ]; then
      "$chrome" --headless --disable-gpu --print-to-pdf="$pdf" "file:///tmp/_a.html" && { echo "chrome -> $pdf"; return; }
    fi
  done
  echo "ERROR: no PDF renderer found (install pandoc, weasyprint, or Chrome)"; exit 1
}
render audit/dpia.md
render audit/ai-risk-assessment.md
render audit/accessibility-report.md
