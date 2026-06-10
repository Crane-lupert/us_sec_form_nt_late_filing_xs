#!/usr/bin/env bash
# Render the V5 SSRN preprint from analysis/paper_v2_en.md to PDF.
#
# Mirrors the sec-comment-letter-alpha / cot_producer pipeline:
#   pandoc 3.9 + xelatex (TeX Live) + citeproc + BibTeX
#
# Usage:
#     bash scripts/render-paper.sh         # renders analysis/paper_v2_en.pdf
#     bash scripts/render-paper.sh kr      # renders analysis/README_KR.md to PDF (CJK font)
#
# Prerequisites:
#     - pandoc >= 3.0 (https://pandoc.org/installing.html)
#     - xelatex (TeX Live 2022 or MiKTeX 2024+)
#     - For KR PDF: Malgun Gothic font installed (default on Windows 10+; macOS users
#       can substitute with "Apple SD Gothic Neo")
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ANALYSIS_DIR="$REPO_ROOT/analysis"
TARGET="${1:-en}"

cd "$REPO_ROOT/analysis"

case "$TARGET" in
  en|EN)
    INPUT="paper_v2_en.md"
    OUTPUT="paper_v2_en.pdf"
    EXTRA_OPTS=()
    ;;
  kr|KR)
    INPUT="README_KR.md"
    OUTPUT="README_KR.pdf"
    # Korean rendering needs a CJK font that ships with the OS.
    EXTRA_OPTS=(
      -V mainfont="Malgun Gothic"
      -V CJKmainfont="Malgun Gothic"
    )
    ;;
  *)
    echo "Usage: $0 [en|kr]" >&2
    exit 1
    ;;
esac

[ -f "$INPUT" ] || { echo "Input not found: $INPUT" >&2; exit 1; }
[ -f "refs.bib" ] || { echo "BibTeX not found: refs.bib" >&2; exit 1; }

echo "Rendering analysis/$INPUT -> analysis/$OUTPUT..."
pandoc "$INPUT" \
  -o "$OUTPUT" \
  --pdf-engine=xelatex \
  --citeproc \
  --bibliography=refs.bib \
  --number-sections \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V linkcolor=blue \
  "${EXTRA_OPTS[@]}"

echo "Done: $OUTPUT"
ls -la "$OUTPUT"
