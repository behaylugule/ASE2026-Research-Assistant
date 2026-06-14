# ASE2026 Paper (ACM SIGPLAN / POPL-style)

This folder contains a conference-style paper matching the **POPL15-TSStack.pdf** template format (ACM `acmart` class, `sigplan` option).

## Files

| File | Purpose |
|------|---------|
| `main.tex` | Full paper source |
| `references.bib` | Bibliography |
| `acmart/` | ACM LaTeX class (from CTAN) |

## Option A — Overleaf (recommended, no local install)

1. Go to [Overleaf](https://www.overleaf.com) → **New Project** → **ACM Conference Proceedings Primary Article Template**
2. Replace the sample `main.tex` content with `docs/paper/main.tex` from this repo
3. Upload `references.bib`
4. Set document class line to:
   ```latex
   \documentclass[sigplan,review,anonymous]{acmart}
   ```
5. Replace **Your Name**, university, and email in `main.tex`
6. **Recompile** → **Download PDF**

## Option B — Local compile (requires TeX Live)

```bash
cd docs/paper/acmart
latex acmart.ins          # generates acmart.cls
cd ..
cp acmart/acmart.cls acmart/ACM-Reference-Format.bst .
pdflatex main
bibtex main
pdflatex main
pdflatex main
# Output: main.pdf
```

Install TeX Live (Ubuntu):

```bash
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-bibtex-extra
```

## Option C — Docker

```bash
cd docs/paper
docker run --rm -v "$(pwd):/work" -w /work texlive/texlive:latest \
  bash -c "cd acmart && latex acmart.ins && cd .. && cp acmart/acmart.cls acmart/ACM-Reference-Format.bst . && pdflatex main && bibtex main && pdflatex main && pdflatex main"
```

First run downloads the TeX Live image (~4 GB).

## Before submission

1. Change `\author{Your Name}` and `\email{...}` in `main.tex`
2. Remove `anonymous` from `\documentclass` if your professor wants your name shown:
   ```latex
   \documentclass[sigplan,review]{acmart}
   ```
3. For single-column manuscript (easier to read), use:
   ```latex
   \documentclass[sigplan,manuscript]{acmart}
   ```

## Reference template

Professor template: **POPL15-TSStack.pdf** — *A Scalable, Correct Time-Stamped Stack* (ACM SIGPLAN POPL 2015 format).
