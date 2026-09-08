# PDF Inspector + Extractor

**Module:** `aurora/documents/pdftool.py` · CLI `aurora/documents/cli.py`
**Tests:** `tests/test_pdftool.py` — 70 passing
**Backend:** PyMuPDF 1.28.2 — **AGPL-3.0, see §6**
**Status:** implemented, wired into `interpreters/universal.py`

---

## 1. Why two modes

**inspect** — *what IS this file?* Structure, encryption, permissions, active
content. Answers "is this safe to open, and may I legally use it?"

**extract** — *what is IN this file?* Text, images, tables, attachments,
metadata, forms, outline.

The split matters because PDFs are an attack surface, not a document format.
The spec permits embedded JavaScript, auto-firing `/OpenAction`, `/Launch`
targets that start external programs, and encrypted payloads. A tool that
ingests untrusted PDFs and reports only page count is lying by omission.

---

## 2. Safety interlock

`extract()` inspects first and **refuses HIGH/CRITICAL documents unless
`force=True`**. This inverts the usual library default, which parses anything.
The safe path should be the default one, because the unsafe path is what
people reach for at 2am during an incident.

```python
res = extract_pdf("invoice.pdf")
# -> errors: ["refusing to extract: risk=critical. Findings: launch(critical)..."]

res = extract_pdf("invoice.pdf", force=True)   # explicit override
```

Risk is the **maximum** finding, never an average — one CRITICAL is not
diluted by nine INFOs. Locked by `test_risk_is_max_not_average`.

### Detections

| Code | Risk | Why it matters |
|---|---|---|
| `launch` | CRITICAL | `/Launch` can start an external program |
| `dangerous_attachment` | CRITICAL | Embedded `.exe`/`.dll`/`.js`/`.lnk` — almost never legitimate |
| `js`, `js_short` | HIGH | Embedded JavaScript; common exploit vector |
| `submit_form` | HIGH | Can exfiltrate entered form data to a URL |
| `richmedia` | HIGH | Flash/3D annotations, historically exploit-prone |
| `archive_attachment` | HIGH | Archives smuggle payloads past mail filters |
| `file_url` | HIGH | References the local filesystem |
| `openaction`, `additional_actions` | MEDIUM | Fires before the user does anything |
| `internal_url` | MEDIUM | RFC1918/loopback link — SSRF and recon |
| `incremental_updates` | MEDIUM | Prior revisions retained; "redacted" content recoverable |
| `xfa` | MEDIUM | Deprecated, large, vulnerable parser surface |
| `a11y_blocked` | MEDIUM | Blocks screen readers — WCAG/legal problem |
| `unparseable` | HIGH | Parsers disagreeing is itself exploitable |

Every `Finding` carries `evidence` (the xref id or matched string). A scanner
that says "suspicious" without showing why is unusable in an incident —
enforced by `test_findings_carry_evidence`.

### Object-level scanning

Detection walks `xref_object(..., compressed=True)` rather than grepping raw
bytes, because `/ObjStm` hides objects inside compressed streams. A raw
keyword scan misses active content entirely; the presence of object streams
is itself reported as `object_streams`.

---

## 3. Resource limits

PDFs are untrusted input. `Limits` caps file size, pages, text characters,
image count, **pixel count per image**, and total attachment bytes.

The pixel cap is the important one: a 40 KB PDF that decompresses to 12 GB of
raster is a real and common DoS. Oversize files are refused *before* parsing.

---

## 4. Two real bugs the tests caught

**1. `is_encrypted` does not mean "encrypted."**
PyMuPDF's `doc.is_encrypted` means *"still locked right now"* and flips to
`False` the instant a document opens — including owner-password files that
open freely but forbid copying. My permission checks were gated on it, so for
exactly the files where permissions matter, **every check silently no-opped**.

Fixed by detecting `/Encrypt` from the raw trailer (authoritative regardless
of open state) and tracking `encrypted` and `still_locked` separately.
Permission findings now key off `permissions_restricted`. Regression:
`test_owner_only_encryption_opens_empty`.

**2. `"1--2"` parsed as a valid range.**
`partition("-")` yields `("1", "-", "-2")`, so the spec silently became
`1..-2` and was normalised into a reversed range instead of rejected. Now
splits on every hyphen and requires exactly two numeric parts.

Both were failing **open** — the dangerous direction.

---

## 5. Usage

```bash
python -m aurora.documents.cli inspect report.pdf
python -m aurora.documents.cli inspect report.pdf --json --fail-on high
python -m aurora.documents.cli extract report.pdf -o ./out --images --tables --attachments
python -m aurora.documents.cli text    report.pdf --pages 1-5
python -m aurora.documents.cli scan    ./inbox --recursive --fail-on high
```

Exit codes gate a pipeline: `0` clean · `1` error · `2` findings at/above
`--fail-on` · `3` password required · `4` backend missing.

```python
from aurora.documents.pdftool import inspect_pdf, extract_pdf, extract_text

report = inspect_pdf("doc.pdf")
if report.safe_to_extract:
    res = extract_pdf("doc.pdf", want_tables=True, output_dir="./out")
```

Attachment filenames are untrusted: path components are stripped and the name
sanitised, so a crafted `..\..\startup\evil.exe` cannot escape the output
directory (`test_attachment_path_traversal_is_neutralised`).

---

## 6. Licensing — decision required

**PyMuPDF is AGPL-3.0.** If AGENCY OS is distributed *or offered as a network
service*, AGPL obligations propagate to the entire work unless Artifex
commercial licensing is purchased. For a hosted creative-ERP product, the
network clause is the one that bites — AGPL is not "internal use is fine" once
customers reach it over HTTP.

This is a business decision, not a technical one. Containment measures taken:

- `BACKEND_LICENCE = "AGPL-3.0"` is exported so a build gate can assert on it.
- `aurora/documents/__init__.py` does **not** import `pdftool`; the dependency
  is pulled in only when a caller asks for it.
- The interpreter hook imports locally and degrades to metadata-only if absent.

**Deleting `pdftool.py` removes the entire AGPL surface** — nothing else in
`aurora/` imports it implicitly.

If the licence is unacceptable, the swap is `pypdf` (BSD-3) for inspection —
which covers the security-critical path well — at the cost of markedly weaker
text extraction and no `find_tables()`.

---

## 7. Known gaps

- **OCR depends on an external binary.** `--ocr` works when
  `tesseract` is installed (auto-detected). Language packs beyond `eng`
  are left to the operator's Tesseract install.
- **No DOCX/XLSX/PPTX.** `_extract_document` returns metadata-only for
  non-PDF formats rather than pretending.
- **OCR: `--ocr`.** Scanned pages (near-zero text layer with embedded
  images) are rasterised and read with Tesseract. Requires the `tesseract`
  binary; looked up on PATH then standard Windows/Unix locations. Runs
  under `ocr_dpi`, `max_ocr_pages`, and a hard `ocr_timeout_seconds` so a
  huge or hung scan cannot stall extraction. Absent backend is an error,
  not a silent empty page. Language via `--ocr-lang` (default `eng`).
- **Merged/multi-level tables imperfect.** Runs `lines` first, then
  `text`-strategy alignment fallback; heavily-merged or multi-level-header
  grids are still imperfect. Each table records the `strategy` that found it.
- **Pure stdout.** `find_tables()` in PyMuPDF prints an advisory
  ("Consider using the pymupdf_layout package...") to stdout, which would
  corrupt `--json` output and `text` pipe consumers. Extraction runs that
  call under a swallowed stdout; stderr is preserved for real diagnostics.
- **Not thread-safe.** MuPDF documents are not safe to share across threads;
  one `Document` per thread.
- **`safe_to_extract` is a heuristic**, not a verdict. A clean report means
  no *known* pattern matched, not that the file is safe.
