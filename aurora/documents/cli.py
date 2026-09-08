"""
AGENCY OS — PDF inspector/extractor CLI.

    python -m aurora.documents.cli inspect  report.pdf
    python -m aurora.documents.cli inspect  report.pdf --json
    python -m aurora.documents.cli extract  report.pdf -o ./out --images --tables
    python -m aurora.documents.cli text     report.pdf --pages 1-5
    python -m aurora.documents.cli scan     ./inbox --recursive

Exit codes are meaningful so this can gate a pipeline:
    0  clean / success
    1  usage or runtime error
    2  findings at or above --fail-on threshold
    3  password required
    4  backend missing
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from aurora.documents.pdftool import (
    BACKEND, BACKEND_LICENCE, BackendMissing, Limits, PDFExtractor,
    PDFInspector, Risk, _RISK_ORDER, _find_tesseract, parse_page_spec,
    scan_directory,
)

EXIT_OK, EXIT_ERROR, EXIT_FINDINGS, EXIT_LOCKED, EXIT_NO_BACKEND = 0, 1, 2, 3, 4

_RISK_NAMES = [r.value for r in Risk]


def _limits(a) -> Limits:
    lim = Limits()
    if a.max_pages:
        lim.max_pages = a.max_pages
    if a.max_mb:
        lim.max_file_bytes = a.max_mb * 1024 * 1024
    return lim


def _emit(obj, as_json: bool, text: str) -> None:
    print(json.dumps(obj, indent=2, default=str) if as_json else text)


def cmd_inspect(a) -> int:
    insp = PDFInspector(_limits(a))
    report = insp.inspect(a.path, password=a.password)
    _emit(report.to_dict(), a.json, report.summary())

    if report.needs_password:
        return EXIT_LOCKED
    if a.fail_on:
        threshold = Risk(a.fail_on)
        if _RISK_ORDER[report.risk] >= _RISK_ORDER[threshold]:
            if not a.json:
                print(f"\nFAIL: risk {report.risk.value} >= {threshold.value}",
                      file=sys.stderr)
            return EXIT_FINDINGS
    return EXIT_OK


def cmd_extract(a) -> int:
    ex = PDFExtractor(_limits(a))
    pages = parse_page_spec(a.pages) if a.pages else None
    res = ex.extract(
        a.path,
        password=a.password,
        pages=pages,
        want_text=not a.no_text,
        want_tables=a.tables,
        want_images=a.images,
        want_attachments=a.attachments,
        output_dir=a.output,
        force=a.force,
        respect_permissions=a.respect_permissions,
        skip_inspection=a.skip_inspection,
        ocr=a.ocr,
        ocr_lang=a.ocr_lang,
    )

    if res.errors:
        for e in res.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        if any("password" in e for e in res.errors):
            return EXIT_LOCKED
        if any("refusing to extract" in e for e in res.errors):
            return EXIT_FINDINGS
        return EXIT_ERROR

    if a.json:
        print(json.dumps(res.to_dict(include_text=not a.no_text),
                         indent=2, default=str))
        return EXIT_OK

    lines = [
        f"{res.filename}  sha256:{res.sha256[:12]}",
        f"  pages={len(res.pages)}/{res.page_count}  chars={res.char_count:,}"
        f"  images={len(res.images)}  tables={len(res.tables)}"
        f"  attachments={len(res.attachments)}",
    ]
    if res.ocr_pages:
        lines.append(f"  OCR: {res.ocr_pages} page(s) recognised")
    if res.outline:
        lines.append(f"  outline entries: {len(res.outline)}")
    if res.form_data:
        lines.append(f"  form fields: {len(res.form_data)}")
    if res.truncated:
        lines.append("  TRUNCATED — limits reached")
    for w in res.warnings[:20]:
        lines.append(f"  warn: {w}")
    for f in res.written_files[:40]:
        lines.append(f"  wrote: {f}")
    if len(res.written_files) > 40:
        lines.append(f"  ... and {len(res.written_files)-40} more")
    print("\n".join(lines))

    if a.output and not a.no_text:
        out = Path(a.output)
        out.mkdir(parents=True, exist_ok=True)
        tf = out / (Path(res.filename).stem + ".txt")
        tf.write_text(res.text, encoding="utf-8")
        print(f"  wrote: {tf}")
    return EXIT_OK


def cmd_text(a) -> int:
    ex = PDFExtractor(_limits(a))
    pages = parse_page_spec(a.pages) if a.pages else None
    res = ex.extract(a.path, password=a.password, pages=pages,
                     want_text=True, force=a.force,
                     skip_inspection=a.skip_inspection,
                     ocr=a.ocr, ocr_lang=a.ocr_lang)
    if res.errors:
        for e in res.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_LOCKED if any("password" in e for e in res.errors) \
            else EXIT_FINDINGS
    sys.stdout.write(res.text)
    return EXIT_OK


def cmd_scan(a) -> int:
    reports = scan_directory(a.path, recursive=a.recursive, limits=_limits(a))
    if a.json:
        print(json.dumps([r.to_dict() for r in reports], indent=2, default=str))
    else:
        if not reports:
            print("no PDFs found")
            return EXIT_OK
        print(f"{len(reports)} PDF(s), most severe first\n")
        for r in reports:
            flags = ",".join(sorted({f.code for f in r.findings})) or "-"
            print(f"  {r.risk.value:<8} {r.filename[:44]:<44} "
                  f"p={r.page_count:<5} {flags[:60]}")
        worst = max((r.risk for r in reports), key=lambda x: _RISK_ORDER[x])
        print(f"\nworst: {worst.value}")

    if a.fail_on and reports:
        threshold = Risk(a.fail_on)
        worst = max((r.risk for r in reports), key=lambda x: _RISK_ORDER[x])
        if _RISK_ORDER[worst] >= _RISK_ORDER[threshold]:
            return EXIT_FINDINGS
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdftool",
        description="PDF inspector and extractor (AGENCY OS). "
                    f"Backend: {BACKEND} ({BACKEND_LICENCE}).")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--password", help="password for encrypted documents")
    p.add_argument("--max-pages", type=int, help="page ceiling")
    p.add_argument("--max-mb", type=int, help="file size ceiling in MB")
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("inspect", help="structure + security report")
    i.add_argument("path")
    i.add_argument("--fail-on", choices=_RISK_NAMES,
                   help="exit 2 if risk >= this level")
    i.set_defaults(func=cmd_inspect)

    e = sub.add_parser("extract", help="extract content")
    e.add_argument("path")
    e.add_argument("-o", "--output", help="write assets to this directory")
    e.add_argument("--pages", help="page spec, e.g. 1,3,5-8")
    e.add_argument("--images", action="store_true")
    e.add_argument("--tables", action="store_true")
    e.add_argument("--attachments", action="store_true")
    e.add_argument("--no-text", action="store_true")
    e.add_argument("--force", action="store_true",
                   help="extract even if inspection flags HIGH/CRITICAL risk")
    e.add_argument("--respect-permissions", action="store_true",
                   help="honour the document's no-copy flag")
    e.add_argument("--skip-inspection", action="store_true",
                   help="faster, but no safety interlock")
    e.add_argument("--ocr", action="store_true",
                   help="OCR scanned pages (requires Tesseract)"
                   + (" [tesseract found]" if _find_tesseract() else " [tesseract MISSING]"))
    e.add_argument("--ocr-lang", default="eng",
                   help="Tesseract language (default: eng)")
    e.set_defaults(func=cmd_extract)

    t = sub.add_parser("text", help="plain text to stdout")
    t.add_argument("path")
    t.add_argument("--pages")
    t.add_argument("--force", action="store_true")
    t.add_argument("--skip-inspection", action="store_true")
    t.add_argument("--ocr", action="store_true",
                   help="OCR scanned pages"
                   + (" [tesseract found]" if _find_tesseract() else " [tesseract MISSING]"))
    t.add_argument("--ocr-lang", default="eng")
    t.set_defaults(func=cmd_text)

    s = sub.add_parser("scan", help="triage a directory of PDFs")
    s.add_argument("path")
    s.add_argument("-r", "--recursive", action="store_true")
    s.add_argument("--fail-on", choices=_RISK_NAMES)
    s.set_defaults(func=cmd_scan)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except BackendMissing as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_NO_BACKEND
    except FileNotFoundError as e:
        print(f"ERROR: not found: {e}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
