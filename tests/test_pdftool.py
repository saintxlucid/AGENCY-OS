"""
PDF inspector/extractor tests.

Fixtures are built at runtime — no binary blobs in the repo. The hostile
fixtures are hand-written PDF source rather than generated, because the
whole point is to exercise constructs a well-behaved library would not emit.

Run:  python -m unittest tests.test_pdftool -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.documents.pdftool import (  # noqa: E402
    BackendMissing, ExtractionResult, Finding, InspectionReport, Limits,
    PDFExtractor, PDFInspector, Risk, _RISK_ORDER, extract_text, inspect_pdf,
    parse_page_spec, pymupdf, scan_directory,
)
from aurora.documents import cli  # noqa: E402

HAS_BACKEND = pymupdf is not None
skip_no_backend = unittest.skipUnless(HAS_BACKEND, "PyMuPDF not installed")

from aurora.documents.pdftool import _find_tesseract  # noqa: E402
HAS_TESSERACT = _find_tesseract() is not None
HAS_TESSER = HAS_TESSERACT


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

def make_pdf(path: Path, pages=2, text="Hello CRP", meta=None,
             encrypt=None, owner_only=False) -> Path:
    doc = pymupdf.open()
    for i in range(pages):
        pg = doc.new_page()
        pg.insert_text((72, 72 + 14 * 0), f"{text} page {i+1}")
        pg.insert_text((72, 100), "Lorem ipsum dolor sit amet " * 3)
    doc.set_metadata(meta or {"title": "Fixture", "author": "Tests"})

    kwargs = {}
    if encrypt is not None:
        kwargs = dict(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                      owner_pw=encrypt, user_pw=encrypt)
    elif owner_only:
        # Owner password only: opens with an empty user password but forbids
        # copying. The "protected but not confidential" case — and the one
        # that exposed the is_encrypted/still_locked conflation, because
        # PyMuPDF reports is_encrypted == False once such a file is open.
        kwargs = dict(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                      owner_pw="ownersecret",
                      permissions=pymupdf.PDF_PERM_PRINT
                      | pymupdf.PDF_PERM_ACCESSIBILITY)
    doc.save(str(path), **kwargs)
    doc.close()
    return path


def make_raw_pdf(path: Path, body_objects: str, extra_root: str = "") -> Path:
    """
    Hand-rolled PDF. xref offsets are intentionally not recomputed — MuPDF
    repairs such files, which is itself a condition worth testing.
    """
    src = f"""%PDF-1.7
1 0 obj
<< /Type /Catalog /Pages 2 0 R {extra_root} >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 72 720 Td (raw fixture) Tj ET
endstream
endobj
{body_objects}
trailer
<< /Root 1 0 R /Size 9 >>
%%EOF
"""
    path.write_bytes(src.encode("latin-1"))
    return path


def make_js_pdf(path: Path) -> Path:
    return make_raw_pdf(
        path,
        body_objects="""5 0 obj
<< /Type /Action /S /JavaScript /JS (app.alert\\('pwned'\\);) >>
endobj
""",
        extra_root="/OpenAction 5 0 R /Names << /JavaScript 5 0 R >>")


def make_launch_pdf(path: Path) -> Path:
    return make_raw_pdf(
        path,
        body_objects="""5 0 obj
<< /Type /Action /S /Launch /F (cmd.exe) >>
endobj
""",
        extra_root="/OpenAction 5 0 R")


def make_url_pdf(path: Path, url: str) -> Path:
    return make_raw_pdf(
        path,
        body_objects=f"""5 0 obj
<< /Type /Annot /Subtype /Link /A << /S /URI /URI ({url}) >> >>
endobj
""")


def make_attachment_pdf(path: Path, name: str, data: bytes) -> Path:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "has attachment")
    doc.embfile_add(name, data, filename=name, desc="test payload")
    doc.save(str(path))
    doc.close()
    return path


def make_incremental_pdf(path: Path) -> Path:
    make_pdf(path, pages=1, text="v1")
    doc = pymupdf.open(str(path))
    doc.new_page().insert_text((72, 72), "v2 appended")
    doc.save(str(path), incremental=True, encryption=pymupdf.PDF_ENCRYPT_KEEP)
    doc.close()
    return path


def make_table_pdf(path: Path) -> Path:
    doc = pymupdf.open()
    pg = doc.new_page()
    y = 100
    rows = [("Client", "Spend", "Margin"),
            ("Lumen", "42000", "0.56"),
            ("Vero", "18500", "0.41")]
    for r in rows:
        x = 72
        for cell in r:
            pg.insert_text((x, y), cell)
            x += 140
        y += 24
    # Ruling lines give find_tables() a grid to latch onto.
    for i in range(len(rows) + 1):
        pg.draw_line(pymupdf.Point(66, 88 + i * 24),
                     pymupdf.Point(460, 88 + i * 24))
    for i in range(4):
        pg.draw_line(pymupdf.Point(66 + i * 140, 88),
                     pymupdf.Point(66 + i * 140, 88 + len(rows) * 24))
    doc.save(str(path))
    doc.close()
    return path


def make_borderless_table_pdf(path: Path) -> Path:
    """
    A table with no ruling lines whatsoever. `strategy="lines"` finds
    nothing here; only the text-alignment pass does. This is the class of
    grid that real client briefs actually produce.
    """
    doc = pymupdf.open()
    pg = doc.new_page()
    y = 80
    rows = [("Client", "Spend", "Margin"),
            ("Lumen", "42000", "0.56"),
            ("Vero", "18500", "0.41"),
            ("Nova", "990", "0.63")]
    for r in rows:
        x = 72
        for cell in r:
            pg.insert_text((x, y), cell)
            x += 140
        y += 22
    doc.save(str(path))
    doc.close()
    return path


# ═══════════════════════════════════════════════════════════════
# Pure helpers — run without the backend
# ═══════════════════════════════════════════════════════════════

class TestPageSpec(unittest.TestCase):

    CASES = [
        ("1", [1]),
        ("1,3", [1, 3]),
        ("5-8", [5, 6, 7, 8]),
        ("1,3,5-8,12", [1, 3, 5, 6, 7, 8, 12]),
        ("8-5", [5, 6, 7, 8]),
        ("2,2,2", [2]),
        (" 1 , 4 ", [1, 4]),
        ("0,1", [1]),
    ]

    def test_parse(self):
        for spec, expected in self.CASES:
            with self.subTest(spec=spec):
                self.assertEqual(parse_page_spec(spec), expected)

    def test_rejects_garbage(self):
        for bad in ("abc", "1-x", "-", "1--2"):
            with self.subTest(spec=bad):
                with self.assertRaises(ValueError):
                    parse_page_spec(bad)

    def test_rejects_absurd_range(self):
        with self.assertRaises(ValueError):
            parse_page_spec("1-999999999")


class TestRiskModel(unittest.TestCase):

    def test_risk_is_max_not_average(self):
        r = InspectionReport(path="p", filename="f", size_bytes=1, sha256="x")
        r.findings = [
            Finding("a", Risk.INFO, "t", "d"),
            Finding("b", Risk.CRITICAL, "t", "d"),
            Finding("c", Risk.INFO, "t", "d"),
        ]
        self.assertIs(r.risk, Risk.CRITICAL,
                      "one CRITICAL must not be diluted by many INFOs")

    def test_no_findings_is_none(self):
        r = InspectionReport(path="p", filename="f", size_bytes=1, sha256="x")
        self.assertIs(r.risk, Risk.NONE)

    def test_safe_to_extract_requires_readable(self):
        r = InspectionReport(path="p", filename="f", size_bytes=1, sha256="x")
        r.readable = False
        self.assertFalse(r.safe_to_extract)
        r.readable = True
        self.assertTrue(r.safe_to_extract)

    def test_high_risk_blocks_extraction(self):
        r = InspectionReport(path="p", filename="f", size_bytes=1, sha256="x")
        r.readable = True
        r.findings = [Finding("js", Risk.HIGH, "t", "d")]
        self.assertFalse(r.safe_to_extract)

    def test_medium_risk_still_allows(self):
        r = InspectionReport(path="p", filename="f", size_bytes=1, sha256="x")
        r.readable = True
        r.findings = [Finding("x", Risk.MEDIUM, "t", "d")]
        self.assertTrue(r.safe_to_extract)


# ═══════════════════════════════════════════════════════════════
# Inspection
# ═══════════════════════════════════════════════════════════════

@skip_no_backend
class TestInspectClean(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pdf = make_pdf(self.tmp / "clean.pdf", pages=3)

    def test_basic_structure(self):
        r = inspect_pdf(self.pdf)
        self.assertTrue(r.is_pdf)
        self.assertTrue(r.readable)
        self.assertEqual(r.page_count, 3)
        self.assertTrue(r.has_text)
        self.assertGreater(r.object_count, 0)
        self.assertTrue(r.pdf_version.startswith("1."))
        self.assertEqual(len(r.sha256), 64)

    def test_clean_file_is_safe(self):
        r = inspect_pdf(self.pdf)
        self.assertTrue(r.safe_to_extract)
        self.assertLess(_RISK_ORDER[r.risk], _RISK_ORDER[Risk.HIGH])

    def test_metadata_captured(self):
        r = inspect_pdf(self.pdf)
        self.assertEqual(r.metadata.get("title"), "Fixture")

    def test_report_serializes(self):
        d = inspect_pdf(self.pdf).to_dict()
        json.dumps(d)                              # must not raise
        self.assertIn("risk", d)
        self.assertIn("safe_to_extract", d)
        self.assertIsInstance(d["findings"], list)

    def test_summary_is_text(self):
        s = inspect_pdf(self.pdf).summary()
        self.assertIn("clean.pdf", s)
        self.assertIn("risk=", s)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            inspect_pdf(self.tmp / "nope.pdf")

    def test_non_pdf_flagged(self):
        f = self.tmp / "fake.pdf"
        f.write_bytes(b"This is not a PDF at all")
        r = inspect_pdf(f)
        self.assertFalse(r.is_pdf)
        self.assertIn("not_pdf", {x.code for x in r.findings})

    def test_oversize_refused_without_parsing(self):
        lim = Limits(max_file_bytes=10)
        r = PDFInspector(lim).inspect(self.pdf)
        self.assertIn("oversize", {x.code for x in r.findings})
        self.assertEqual(r.page_count, 0, "must not parse an oversize file")


@skip_no_backend
class TestInspectHostile(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _codes(self, path):
        return {f.code for f in inspect_pdf(path).findings}

    def test_javascript_detected(self):
        codes = self._codes(make_js_pdf(self.tmp / "js.pdf"))
        self.assertTrue({"js", "js_short"} & codes,
                        f"JavaScript not detected; got {codes}")

    def test_openaction_detected(self):
        self.assertIn("openaction", self._codes(make_js_pdf(self.tmp / "oa.pdf")))

    def test_launch_action_is_critical(self):
        r = inspect_pdf(make_launch_pdf(self.tmp / "launch.pdf"))
        self.assertIn("launch", {f.code for f in r.findings})
        self.assertIs(r.risk, Risk.CRITICAL)
        self.assertFalse(r.safe_to_extract)

    def test_js_pdf_refuses_extraction(self):
        r = inspect_pdf(make_js_pdf(self.tmp / "js2.pdf"))
        self.assertFalse(r.safe_to_extract)

    def test_findings_carry_evidence(self):
        r = inspect_pdf(make_launch_pdf(self.tmp / "l2.pdf"))
        f = next(x for x in r.findings if x.code == "launch")
        self.assertTrue(f.evidence, "a finding without evidence is unverifiable")

    def test_file_url_flagged(self):
        codes = self._codes(make_url_pdf(self.tmp / "u.pdf",
                                         "file:///C:/Windows/System32/x"))
        self.assertIn("file_url", codes)

    def test_internal_url_flagged(self):
        codes = self._codes(make_url_pdf(self.tmp / "i.pdf",
                                         "http://192.168.1.10/beacon"))
        self.assertIn("internal_url", codes)

    def test_public_url_is_only_info(self):
        r = inspect_pdf(make_url_pdf(self.tmp / "p.pdf", "https://example.com/a"))
        self.assertNotIn("internal_url", {f.code for f in r.findings})
        self.assertTrue(any("example.com" in u for u in r.urls))

    def test_executable_attachment_is_critical(self):
        p = make_attachment_pdf(self.tmp / "exe.pdf", "invoice.exe", b"MZ\x90\x00")
        r = inspect_pdf(p)
        self.assertIn("dangerous_attachment", {f.code for f in r.findings})
        self.assertIs(r.risk, Risk.CRITICAL)

    def test_archive_attachment_is_high(self):
        p = make_attachment_pdf(self.tmp / "zip.pdf", "docs.zip", b"PK\x03\x04")
        codes = {f.code for f in inspect_pdf(p).findings}
        self.assertIn("archive_attachment", codes)

    def test_benign_attachment_not_flagged_dangerous(self):
        p = make_attachment_pdf(self.tmp / "txt.pdf", "notes.txt", b"hello")
        r = inspect_pdf(p)
        codes = {f.code for f in r.findings}
        self.assertNotIn("dangerous_attachment", codes)
        self.assertEqual(r.embedded_file_count, 1)
        self.assertEqual(r.embedded_files[0]["name"], "notes.txt")

    def test_incremental_updates_detected(self):
        r = inspect_pdf(make_incremental_pdf(self.tmp / "inc.pdf"))
        self.assertTrue(r.has_incremental_updates)
        self.assertIn("incremental_updates", {f.code for f in r.findings})

    def test_scan_directory_sorts_worst_first(self):
        make_pdf(self.tmp / "a_clean.pdf")
        make_launch_pdf(self.tmp / "z_evil.pdf")
        reports = scan_directory(self.tmp, recursive=False)
        self.assertGreaterEqual(len(reports), 2)
        self.assertIs(reports[0].risk, Risk.CRITICAL)
        self.assertEqual(reports[0].filename, "z_evil.pdf")


@skip_no_backend
class TestEncryption(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_password_required_reported(self):
        p = make_pdf(self.tmp / "locked.pdf", encrypt="s3cret")
        r = inspect_pdf(p)
        self.assertTrue(r.encrypted)
        self.assertTrue(r.needs_password)
        self.assertFalse(r.safe_to_extract)
        self.assertIn("password_required", {f.code for f in r.findings})

    def test_correct_password_unlocks(self):
        p = make_pdf(self.tmp / "locked2.pdf", encrypt="s3cret")
        r = inspect_pdf(p, password="s3cret")
        self.assertFalse(r.needs_password)
        self.assertTrue(r.readable)
        self.assertEqual(r.page_count, 2)

    def test_owner_only_encryption_opens_empty(self):
        """
        Regression: PyMuPDF's is_encrypted reports False for a file that has
        an /Encrypt dict but opens without a password. Detection must come
        from the raw trailer, or every permission check silently no-ops.
        """
        p = make_pdf(self.tmp / "owner.pdf", owner_only=True)
        r = inspect_pdf(p)
        self.assertTrue(r.encrypted, "must detect /Encrypt from raw bytes")
        self.assertFalse(r.still_locked, "opens without a password")
        self.assertFalse(r.needs_password)
        self.assertTrue(r.readable)

    def test_permissions_surfaced(self):
        p = make_pdf(self.tmp / "perm.pdf", owner_only=True)
        r = inspect_pdf(p)
        self.assertIn("copy", r.permissions)
        self.assertFalse(r.permissions["copy"])
        self.assertTrue(r.permissions_restricted)
        self.assertIn("copy_restricted", {f.code for f in r.findings})

    def test_unrestricted_pdf_has_no_permission_findings(self):
        p = make_pdf(self.tmp / "free.pdf")
        r = inspect_pdf(p)
        self.assertFalse(r.permissions_restricted)
        codes = {f.code for f in r.findings}
        self.assertNotIn("copy_restricted", codes)
        self.assertNotIn("a11y_blocked", codes)

    def test_extract_blocked_when_respecting_permissions(self):
        p = make_pdf(self.tmp / "perm2.pdf", owner_only=True)
        res = PDFExtractor().extract(p, respect_permissions=True)
        self.assertTrue(res.errors)
        self.assertIn("forbids copying", res.errors[0])

    def test_extract_allowed_when_not_respecting(self):
        p = make_pdf(self.tmp / "perm3.pdf", owner_only=True)
        res = PDFExtractor().extract(p, respect_permissions=False)
        self.assertFalse(res.errors)
        self.assertIn("Hello CRP", res.text)


# ═══════════════════════════════════════════════════════════════
# Extraction
# ═══════════════════════════════════════════════════════════════

@skip_no_backend
class TestExtract(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pdf = make_pdf(self.tmp / "doc.pdf", pages=4)

    def test_text_extracted(self):
        res = PDFExtractor().extract(self.pdf)
        self.assertEqual(len(res.pages), 4)
        self.assertIn("Hello CRP", res.text)
        self.assertGreater(res.char_count, 0)

    def test_page_numbers_are_one_based(self):
        res = PDFExtractor().extract(self.pdf)
        self.assertEqual([p.number for p in res.pages], [1, 2, 3, 4])

    def test_page_selection(self):
        res = PDFExtractor().extract(self.pdf, pages=[2, 4])
        self.assertEqual([p.number for p in res.pages], [2, 4])
        self.assertIn("page 2", res.text)
        self.assertNotIn("page 3", res.text)

    def test_out_of_range_page_warns_not_crashes(self):
        res = PDFExtractor().extract(self.pdf, pages=[1, 99])
        self.assertEqual([p.number for p in res.pages], [1])
        self.assertTrue(any("out of range" in w for w in res.warnings))

    def test_convenience_text_helper(self):
        self.assertIn("Hello CRP", extract_text(self.pdf))

    def test_inspection_embedded_in_result(self):
        res = PDFExtractor().extract(self.pdf)
        self.assertIsNotNone(res.inspection)
        self.assertIn("risk", res.inspection)

    def test_skip_inspection_omits_report(self):
        res = PDFExtractor().extract(self.pdf, skip_inspection=True)
        self.assertIsNone(res.inspection)
        self.assertIn("Hello CRP", res.text)

    def test_text_budget_truncates(self):
        ex = PDFExtractor(Limits(max_text_chars=30))
        res = ex.extract(self.pdf)
        self.assertTrue(res.truncated)
        self.assertLessEqual(res.char_count, 30)

    def test_page_limit_truncates(self):
        ex = PDFExtractor(Limits(max_pages=2))
        res = ex.extract(self.pdf)
        self.assertTrue(res.truncated)
        self.assertEqual(len(res.pages), 2)

    def test_result_serializes(self):
        res = PDFExtractor().extract(self.pdf)
        json.dumps(res.to_dict(), default=str)

    def test_can_omit_text_from_dict(self):
        res = PDFExtractor().extract(self.pdf)
        d = res.to_dict(include_text=False)
        self.assertNotIn("text", d["pages"][0])

    def test_page_geometry_recorded(self):
        res = PDFExtractor().extract(self.pdf, pages=[1])
        self.assertGreater(res.pages[0].width, 0)
        self.assertGreater(res.pages[0].height, 0)


@skip_no_backend
class TestExtractSafetyInterlock(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_refuses_dangerous_pdf_by_default(self):
        p = make_launch_pdf(self.tmp / "evil.pdf")
        res = PDFExtractor().extract(p)
        self.assertTrue(res.errors)
        self.assertIn("refusing to extract", res.errors[0])
        self.assertEqual(res.pages, [])

    def test_force_overrides(self):
        p = make_launch_pdf(self.tmp / "evil2.pdf")
        res = PDFExtractor().extract(p, force=True)
        self.assertFalse(res.errors)
        self.assertGreater(len(res.pages), 0)

    def test_refusal_names_the_findings(self):
        p = make_launch_pdf(self.tmp / "evil3.pdf")
        res = PDFExtractor().extract(p)
        self.assertIn("launch", res.errors[0])

    def test_locked_pdf_reports_password_error(self):
        p = make_pdf(self.tmp / "lk.pdf", encrypt="pw")
        res = PDFExtractor().extract(p)
        self.assertTrue(any("password" in e for e in res.errors))

    def test_locked_pdf_extracts_with_password(self):
        p = make_pdf(self.tmp / "lk2.pdf", encrypt="pw")
        res = PDFExtractor().extract(p, password="pw")
        self.assertFalse(res.errors)
        self.assertIn("Hello CRP", res.text)


@skip_no_backend
class TestExtractAssets(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.out = self.tmp / "out"

    def test_attachments_extracted_to_disk(self):
        p = make_attachment_pdf(self.tmp / "a.pdf", "notes.txt", b"payload-here")
        res = PDFExtractor().extract(p, want_attachments=True,
                                     output_dir=self.out)
        self.assertEqual(len(res.attachments), 1)
        f = Path(res.attachments[0]["file"])
        self.assertTrue(f.exists())
        self.assertEqual(f.read_bytes(), b"payload-here")

    def test_attachment_path_traversal_is_neutralised(self):
        evil = "..\\..\\..\\Windows\\System32\\evil.dll"
        p = make_attachment_pdf(self.tmp / "trav.pdf", evil, b"x")
        res = PDFExtractor().extract(p, want_attachments=True,
                                     output_dir=self.out, force=True)
        if res.attachments and "file" in res.attachments[0]:
            written = Path(res.attachments[0]["file"]).resolve()
            self.assertEqual(written.parent, self.out.resolve(),
                             "attachment escaped the output directory")

    def test_attachment_hash_recorded(self):
        p = make_attachment_pdf(self.tmp / "h.pdf", "x.bin", b"abc")
        res = PDFExtractor().extract(p, want_attachments=True)
        import hashlib
        self.assertEqual(res.attachments[0]["sha256"],
                         hashlib.sha256(b"abc").hexdigest())

    def test_tables_extracted(self):
        p = make_table_pdf(self.tmp / "t.pdf")
        res = PDFExtractor().extract(p, want_tables=True)
        self.assertTrue(res.tables, "no tables found in ruled grid fixture")
        flat = json.dumps(res.tables[0]["data"])
        self.assertIn("Lumen", flat)

    def test_borderless_table_found_via_text_strategy(self):
        """
        Ruling-line detection misses borderless grids entirely; the text
        alignment pass is the fallback. A table without lines must still be
        extracted — this is the shape of real client briefs.
        """
        p = make_borderless_table_pdf(self.tmp / "borderless.pdf")
        res = PDFExtractor().extract(p, want_tables=True)
        self.assertTrue(res.tables,
                        "borderless grid not detected by any strategy")
        data = res.tables[0]["data"]
        flat = json.dumps(data)
        self.assertIn("Lumen", flat)
        self.assertIn("Vero", flat)
        self.assertIn("strategy", res.tables[0])
        self.assertIn(res.tables[0]["strategy"], {"lines", "text"})

    def test_stdout_stays_clean_during_table_extraction(self):
        """
        PyMuPDF's find_tables() prints an advisory ("Consider using the
        pymupdf_layout package...") to stdout. That breaks --json consumers
        and pipe output. Extraction must not leak it.
        """
        import io, contextlib
        p = make_table_pdf(self.tmp / "quiet.pdf")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = PDFExtractor().extract(p, want_tables=True)
        self.assertTrue(res.tables, "sanity: tables must be found")
        out = buf.getvalue()
        self.assertNotIn("pymupdf_layout", out)
        self.assertNotIn("Consider using", out)
        self.assertEqual(out, "", "extraction must write nothing to stdout")

    def test_images_respect_pixel_limit(self):
        doc = pymupdf.open()
        pg = doc.new_page()
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 300, 300))
        pg.insert_image(pymupdf.Rect(0, 0, 300, 300), pixmap=pix)
        p = self.tmp / "img.pdf"
        doc.save(str(p))
        doc.close()

        ex = PDFExtractor(Limits(max_image_pixels=10))
        res = ex.extract(p, want_images=True, output_dir=self.out)
        self.assertEqual(res.images, [])
        self.assertTrue(any("pixel limit" in w for w in res.warnings))

    def test_images_extracted_when_within_limits(self):
        doc = pymupdf.open()
        pg = doc.new_page()
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 60, 60))
        pg.insert_image(pymupdf.Rect(0, 0, 60, 60), pixmap=pix)
        p = self.tmp / "img2.pdf"
        doc.save(str(p))
        doc.close()

        res = PDFExtractor().extract(p, want_images=True, output_dir=self.out)
        self.assertTrue(res.images)
        self.assertTrue(Path(res.images[0]["file"]).exists())


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# OCR
# ═══════════════════════════════════════════════════════════════

def make_scanned_pdf(path: Path, phrase: str = "INVOICE NO 8842") -> Path:
    """A rasterised page: no text layer at all, just a pixel image with
    the phrase rendered into it. The real-world shape of a scanned brief."""
    img = pymupdf.open()
    pg = img.new_page(width=600, height=200)
    pg.insert_text((40, 110), phrase, fontsize=28)
    pix = pg.get_pixmap(dpi=150)
    png = path.with_suffix(".png")
    pix.save(str(png))
    doc = pymupdf.open()
    doc.new_page(width=600, height=200).insert_image(
        pymupdf.Rect(0, 0, 600, 200), filename=str(png))
    doc.save(str(path))
    doc.close()
    png.unlink()
    return path


@skip_no_backend
class TestOCR(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pdf = make_pdf(self.tmp / "text.pdf", pages=1)
        self.scan = make_scanned_pdf(self.tmp / "scan.pdf")

    def test_scanned_pdf_has_no_text_layer(self):
        r = inspect_pdf(self.scan)
        self.assertFalse(r.has_text)
        self.assertTrue(r.likely_scanned)

    def test_text_pdf_not_ocred(self):
        res = PDFExtractor().extract(self.pdf, ocr=True)
        self.assertEqual(res.ocr_pages, 0)
        self.assertFalse(res.pages[0].ocr)
        self.assertIn("Hello CRP", res.text)

    @unittest.skipUnless(HAS_TESSERACT, "Tesseract not installed")
    def test_ocr_recovers_scanned_text(self):
        res = PDFExtractor().extract(self.scan, ocr=True)
        self.assertEqual(res.ocr_pages, 1)
        self.assertTrue(res.pages[0].ocr)
        self.assertIn("8842", res.text)

    @unittest.skipUnless(HAS_TESSERACT, "Tesseract not installed")
    def test_extract_text_convenience_has_ocr(self):
        t = extract_text(self.scan, ocr=True)
        self.assertIn("8842", t)

    def test_ocr_missing_backend_is_an_error(self):
        with unittest.mock.patch("aurora.documents.pdftool._find_tesseract",
                                 return_value=None):
            res = PDFExtractor().extract(self.scan, ocr=True)
            self.assertTrue(res.errors)
            self.assertIn("tesseract", res.errors[0].lower())

    def test_ocr_available_flag_reflects_backend(self):
        res = PDFExtractor().extract(self.scan, ocr=False)
        self.assertIs(res.ocr_available, HAS_TESSER)

    def test_ocr_respects_page_cap(self):
        ex = PDFExtractor(Limits(max_ocr_pages=1, ocr_dpi=40))
        res = ex.extract(self.scan, ocr=True)
        self.assertLessEqual(res.ocr_pages, 1)


@skip_no_backend
class TestCLI(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.clean = make_pdf(self.tmp / "clean.pdf")
        self.evil = make_launch_pdf(self.tmp / "evil.pdf")

    def test_inspect_clean_exit_zero(self):
        self.assertEqual(cli.main(["inspect", str(self.clean)]), cli.EXIT_OK)

    def test_inspect_json_is_valid(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.main(["--json", "inspect", str(self.clean)])
        json.loads(buf.getvalue())

    def test_fail_on_gates_pipeline(self):
        code = cli.main(["inspect", str(self.evil), "--fail-on", "high"])
        self.assertEqual(code, cli.EXIT_FINDINGS)

    def test_fail_on_passes_clean_file(self):
        code = cli.main(["inspect", str(self.clean), "--fail-on", "high"])
        self.assertEqual(code, cli.EXIT_OK)

    def test_locked_returns_locked_code(self):
        p = make_pdf(self.tmp / "lk.pdf", encrypt="pw")
        self.assertEqual(cli.main(["inspect", str(p)]), cli.EXIT_LOCKED)

    def test_extract_refusal_exit_code(self):
        code = cli.main(["extract", str(self.evil)])
        self.assertEqual(code, cli.EXIT_FINDINGS)

    def test_extract_writes_text_file(self):
        out = self.tmp / "o"
        code = cli.main(["extract", str(self.clean), "-o", str(out)])
        self.assertEqual(code, cli.EXIT_OK)
        self.assertTrue((out / "clean.txt").exists())

    def test_text_subcommand_to_stdout(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.main(["text", str(self.clean)])
        self.assertIn("Hello CRP", buf.getvalue())

    def test_scan_directory(self):
        code = cli.main(["scan", str(self.tmp), "--fail-on", "critical"])
        self.assertEqual(code, cli.EXIT_FINDINGS)

    def test_missing_file_exit_error(self):
        self.assertEqual(cli.main(["inspect", str(self.tmp / "nope.pdf")]),
                         cli.EXIT_ERROR)

    def test_bad_page_spec_exit_error(self):
        code = cli.main(["extract", str(self.clean), "--pages", "abc"])
        self.assertEqual(code, cli.EXIT_ERROR)

    def test_extract_ocr_flag_accepted(self):
        code = cli.main(["extract", str(self.clean), "--ocr"])
        self.assertEqual(code, cli.EXIT_OK)


if __name__ == "__main__":
    unittest.main(verbosity=2)
