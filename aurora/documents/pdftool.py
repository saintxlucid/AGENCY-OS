"""
AGENCY OS — PDF Inspector + Extractor

Two jobs, deliberately separated:

  inspect  — what IS this file? Structure, encryption, permissions, and
             active content (JavaScript, launch actions, embedded files).
             Answers "is this safe to open and can I legally use it?"

  extract  — what is IN this file? Text, images, tables, attachments,
             metadata, form fields, outline.
             Answers "give me the content."

Design stance: PDFs are an attack surface, not a document format. The spec
permits embedded JavaScript, auto-executing OpenActions, external launch
targets, and encrypted payloads. Any tool that ingests untrusted PDFs and
reports only page count is lying by omission. Inspection is therefore the
default posture, and extraction refuses to touch active content.

  LICENCE WARNING
  ---------------
  This module depends on PyMuPDF, which is AGPL-3.0. If AGENCY OS is
  distributed or offered as a network service, AGPL obligations propagate
  to the whole work unless Artifex commercial licensing is purchased.
  This is a business decision, not a technical one. `BACKEND_LICENCE`
  below is exported so a build gate can assert on it.

  Nothing else in aurora/ imports this module implicitly; the interpreter
  hook degrades gracefully if it is absent, so removing this one file
  removes the AGPL surface entirely.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import zlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

try:
    import pymupdf                      # PyMuPDF >= 1.24 preferred spelling
except ImportError:                     # pragma: no cover
    try:
        import fitz as pymupdf          # legacy import name
    except ImportError:
        pymupdf = None

BACKEND = "pymupdf"
BACKEND_LICENCE = "AGPL-3.0"            # assert on this in a build gate


class BackendMissing(RuntimeError):
    """PyMuPDF is not installed."""


def _require_backend() -> None:
    if pymupdf is None:
        raise BackendMissing(
            "PyMuPDF is required. Install with: pip install pymupdf\n"
            "Note: PyMuPDF is AGPL-3.0 — see the licence warning in this module."
        )


def _now() -> str:
    return datetime.now().isoformat()


_TESSERACT_CANDIDATES = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"/usr/bin/tesseract",
    r"/usr/local/bin/tesseract",
    r"/opt/homebrew/bin/tesseract",
]


def _find_tesseract() -> Optional[str]:
    """Locate the Tesseract binary. Checks PATH first, then the Windows
    and Unix install locations. Returns None when absent — OCR must
    degrade gracefully rather than hard-depend on an external binary."""
    exe = shutil.which("tesseract")
    if exe:
        return exe
    for cand in _TESSERACT_CANDIDATES:
        if os.path.isfile(cand):
            return cand
    return None


@contextlib.contextmanager
def _silenced_stdout():
    """
    PyMuPDF's find_tables() prints an advisory ("Consider using the
    pymupdf_layout package...") to *stdout*. That single line corrupts
    `--json` output and `text` pipe consumers. Moments like that are why
    machine-facing commands must own their streams: we run find_tables
    inside a swallowed stdout instead of shipping a warning that no one
    asked for.

    Only stdout is redirected: stderr is left alone so real diagnostics
    (including our own warnings) still surface.
    """
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink):
            yield sink
    finally:
        pass


# ═══════════════════════════════════════════════════════════════
# Limits — a PDF is untrusted input
# ═══════════════════════════════════════════════════════════════

@dataclass
class Limits:
    """
    Resource ceilings. Defaults are generous for real documents and hostile
    to decompression bombs. A 40 KB PDF that expands to 12 GB of pixels is a
    real and common denial-of-service; refusing it is correct behaviour.
    """
    max_file_bytes: int = 512 * 1024 * 1024       # 512 MB on disk
    max_pages: int = 5_000
    max_text_chars: int = 50_000_000              # ~50 MB of text
    max_images: int = 5_000
    max_image_pixels: int = 80_000_000            # ~80 MP per image
    max_embedded_bytes: int = 256 * 1024 * 1024   # total attachment payload
    max_extract_seconds: float = 300.0
    ocr_dpi: int = 150                            # render resolution for OCR
    max_ocr_pages: int = 500                      # OCR budget per document
    ocr_timeout_seconds: float = 60.0


class LimitExceeded(Exception):
    """Extraction stopped because a resource ceiling was hit."""


# ═══════════════════════════════════════════════════════════════
# Risk model
# ═══════════════════════════════════════════════════════════════

class Risk(Enum):
    NONE = "none"
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_RISK_ORDER = {r: i for i, r in enumerate(
    [Risk.NONE, Risk.INFO, Risk.LOW, Risk.MEDIUM, Risk.HIGH, Risk.CRITICAL])}


@dataclass
class Finding:
    """
    One observation about the file.

    `evidence` carries the raw substring or object id that triggered it, so a
    reviewer can verify rather than trust. A scanner that says "suspicious"
    without showing why is unusable in an incident.
    """
    code: str
    risk: Risk
    title: str
    detail: str
    evidence: List[str] = field(default_factory=list)
    count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["risk"] = self.risk.value
        return d


# Object-level keys that indicate active or external content.
# Matched against raw xref object source, which is why this catches
# constructs that the high-level API hides.
_ACTIVE_KEYS: List[Tuple[str, str, Risk, str]] = [
    ("/JavaScript", "js", Risk.HIGH,
     "Embedded JavaScript. Common vector for exploit chains and phishing."),
    ("/JS", "js_short", Risk.HIGH,
     "JavaScript action (/JS)."),
    ("/OpenAction", "openaction", Risk.MEDIUM,
     "Action fires automatically on open, before the user does anything."),
    ("/AA", "additional_actions", Risk.MEDIUM,
     "Additional-actions dictionary: triggers on page open/close or field events."),
    ("/Launch", "launch", Risk.CRITICAL,
     "Launch action can start an external program."),
    ("/EmbeddedFile", "embedded_file", Risk.MEDIUM,
     "Embedded file payload."),
    ("/RichMedia", "richmedia", Risk.HIGH,
     "RichMedia annotation (Flash/3D). Historically exploit-prone."),
    ("/Movie", "movie", Risk.MEDIUM, "Movie annotation."),
    ("/Sound", "sound", Risk.LOW, "Sound annotation."),
    ("/GoToR", "goto_remote", Risk.MEDIUM, "Remote go-to action (external file)."),
    ("/SubmitForm", "submit_form", Risk.HIGH,
     "Form submission action can exfiltrate entered data to a URL."),
    ("/ImportData", "import_data", Risk.MEDIUM, "Imports form data from a file."),
    ("/URI", "uri", Risk.INFO, "External URI link."),
    ("/XFA", "xfa", Risk.MEDIUM,
     "XFA form. Large, deprecated, historically vulnerable parser surface."),
]

_URL_RE = re.compile(rb"(?:https?|ftp|file)://[^\s<>()\[\]{}\"']{4,400}")
_PRIVATE_HOST_RE = re.compile(
    r"^(?:localhost|127\.|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|169\.254\.|\[::1\])",
    re.I)

# A page with fewer than this many extractable characters is treated as a
# candidate for OCR — scanners and photo-briefs normally produce near-zero
# chars along with one or more embedded images.
_OCR_MIN_CHARS = 50


# ═══════════════════════════════════════════════════════════════
# Inspection report
# ═══════════════════════════════════════════════════════════════

@dataclass
class InspectionReport:
    path: str
    filename: str
    size_bytes: int
    sha256: str

    is_pdf: bool = False
    readable: bool = False
    pdf_version: Optional[str] = None
    page_count: int = 0
    object_count: int = 0

    # Security posture
    #
    # `encrypted` means "this file carries an /Encrypt dictionary", which is
    # NOT what PyMuPDF's doc.is_encrypted returns. That property means "the
    # document is still locked right now" and flips to False the moment the
    # file opens — including for owner-password files that open freely but
    # restrict copying. Conflating the two silently disables every
    # permission check, so the two states are tracked separately here.
    encrypted: bool = False
    still_locked: bool = False
    needs_password: bool = False
    unlocked_with_empty_password: bool = False
    encryption_method: Optional[str] = None
    permissions: Dict[str, bool] = field(default_factory=dict)
    permissions_restricted: bool = False

    # Integrity
    repaired: bool = False
    linearized: bool = False
    has_incremental_updates: bool = False
    update_generations: int = 0

    # Content inventory
    metadata: Dict[str, Any] = field(default_factory=dict)
    has_text: bool = False
    likely_scanned: bool = False
    image_count: int = 0
    embedded_file_count: int = 0
    embedded_files: List[Dict[str, Any]] = field(default_factory=list)
    form_fields: int = 0
    annotations: int = 0
    outline_entries: int = 0
    fonts: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)

    findings: List[Finding] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    inspected_at: str = field(default_factory=_now)
    backend: str = BACKEND
    backend_licence: str = BACKEND_LICENCE

    # ─── Derived ───

    @property
    def risk(self) -> Risk:
        """Highest single finding. Deliberately not an average — one
        CRITICAL is not cancelled out by nine INFOs."""
        if not self.findings:
            return Risk.NONE
        return max((f.risk for f in self.findings), key=lambda r: _RISK_ORDER[r])

    @property
    def safe_to_extract(self) -> bool:
        """
        Whether automated extraction should proceed unattended.
        Conservative by design: a human can always override with --force.
        """
        return (self.readable
                and not self.needs_password
                and _RISK_ORDER[self.risk] < _RISK_ORDER[Risk.HIGH])

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["findings"] = [f.to_dict() for f in self.findings]
        d["risk"] = self.risk.value
        d["safe_to_extract"] = self.safe_to_extract
        return d

    def summary(self) -> str:
        bits = [
            f"{self.filename}  {self.size_bytes:,}B  sha256:{self.sha256[:12]}",
            f"  risk={self.risk.value}  pages={self.page_count}  "
            f"objects={self.object_count}  pdf={self.pdf_version or '?'}",
        ]
        if self.encrypted:
            bits.append(f"  encrypted={self.encryption_method or 'yes'}"
                        + ("  (opened with empty password)"
                           if self.unlocked_with_empty_password else ""))
        if self.needs_password:
            bits.append("  LOCKED — password required")
        if self.likely_scanned:
            bits.append("  likely scanned (little/no extractable text)")
        for f in sorted(self.findings, key=lambda x: -_RISK_ORDER[x.risk]):
            bits.append(f"  [{f.risk.value:<8}] {f.code:<18} {f.title}"
                        + (f"  x{f.count}" if f.count > 1 else ""))
        return "\n".join(bits)


# ═══════════════════════════════════════════════════════════════
# Inspector
# ═══════════════════════════════════════════════════════════════

class PDFInspector:
    """
    Structural and security inspection. Never renders, never executes,
    never follows a URL. Read-only against bytes already on disk.
    """

    def __init__(self, limits: Optional[Limits] = None):
        self.limits = limits or Limits()

    def inspect(self, path: os.PathLike | str,
                password: Optional[str] = None) -> InspectionReport:
        _require_backend()
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(p)

        size = p.stat().st_size
        report = InspectionReport(
            path=str(p.resolve()), filename=p.name, size_bytes=size,
            sha256=self._sha256(p),
        )

        if size > self.limits.max_file_bytes:
            report.errors.append(
                f"file exceeds max_file_bytes ({size:,} > "
                f"{self.limits.max_file_bytes:,}); refusing to parse")
            report.findings.append(Finding(
                "oversize", Risk.MEDIUM, "File exceeds size limit",
                "Refused to parse. Raise Limits.max_file_bytes to override."))
            return report

        raw = p.read_bytes()
        report.is_pdf = raw[:5] == b"%PDF-"
        if not report.is_pdf:
            report.findings.append(Finding(
                "not_pdf", Risk.MEDIUM, "Missing %PDF- header",
                "File does not begin with a PDF magic number. It may be "
                "mislabelled, corrupt, or deliberately disguised.",
                evidence=[repr(raw[:16])]))

        # Header/structure checks run on raw bytes: they must work even if
        # the high-level parser refuses the document.
        self._inspect_raw(raw, report)

        doc = None
        try:
            doc = pymupdf.open(stream=raw, filetype="pdf")
        except Exception as e:
            report.errors.append(f"open failed: {type(e).__name__}: {e}")
            report.findings.append(Finding(
                "unparseable", Risk.HIGH, "Document could not be parsed",
                f"{type(e).__name__}: {e}. Malformed structure is itself a "
                "signal — parsers disagree, and that disagreement is exploitable."))
            return report

        try:
            self._inspect_doc(doc, report, password)
        except Exception as e:                       # pragma: no cover
            report.errors.append(f"inspect failed: {type(e).__name__}: {e}")
        finally:
            doc.close()

        return report

    # ─── Raw byte layer ───

    def _inspect_raw(self, raw: bytes, report: InspectionReport) -> None:
        m = re.match(rb"%PDF-(\d\.\d)", raw[:16])
        if m:
            report.pdf_version = m.group(1).decode("ascii", "replace")

        # Multiple EOF markers mean incremental updates: earlier revisions of
        # the document are still present in the file. That is how "redacted"
        # documents leak their originals.
        eofs = raw.count(b"%%EOF")
        if eofs > 1:
            report.has_incremental_updates = True
            report.update_generations = eofs
            report.findings.append(Finding(
                "incremental_updates", Risk.MEDIUM,
                f"{eofs} revisions present in file",
                "Prior document revisions are retained. Content believed "
                "removed or redacted may still be recoverable from earlier "
                "generations.", count=eofs))

        if b"/Linearized" in raw[:4096]:
            report.linearized = True

        # Authoritative encryption test. The trailer's /Encrypt entry is
        # present whether or not the document currently needs a password,
        # which is exactly the distinction the high-level API loses.
        if b"/Encrypt" in raw:
            report.encrypted = True
            m = re.search(rb"/Encrypt.{0,400}?/V\s+(\d)", raw, re.S)
            if m:
                report.encryption_method = f"V{m.group(1).decode()}"
            m2 = re.search(rb"/CF\s*<<.{0,200}?/CFM\s*/(\w+)", raw, re.S)
            if m2:
                report.encryption_method = m2.group(1).decode("ascii", "replace")

        # ObjStm hides objects inside compressed streams, so a naive
        # keyword scan of the raw file can miss active content entirely.
        if b"/ObjStm" in raw:
            report.findings.append(Finding(
                "object_streams", Risk.INFO, "Compressed object streams present",
                "Objects are stored inside /ObjStm. Raw keyword scanning alone "
                "is insufficient; object-level inspection is required."))

    # ─── Document layer ───

    def _inspect_doc(self, doc, report: InspectionReport,
                     password: Optional[str]) -> None:
        # doc.is_encrypted == "still locked", not "has encryption".
        # report.encrypted was already set authoritatively from the raw
        # trailer; only OR it here so a stream-only path still works.
        report.still_locked = bool(doc.is_encrypted)
        report.encrypted = report.encrypted or bool(doc.is_encrypted)
        report.needs_password = bool(doc.needs_pass)

        if doc.needs_pass:
            # An empty password that works is a real finding: the document
            # advertises itself as protected but is not.
            if doc.authenticate(""):
                report.unlocked_with_empty_password = True
                report.needs_password = False
                report.findings.append(Finding(
                    "empty_password", Risk.LOW,
                    "Encrypted but opens with an empty password",
                    "Encryption is present for permissions enforcement only; "
                    "it provides no confidentiality."))
            elif password is not None and doc.authenticate(password):
                report.needs_password = False
            else:
                report.findings.append(Finding(
                    "password_required", Risk.INFO, "Password required",
                    "Supply --password to inspect contents. Structural "
                    "inspection is limited until unlocked."))
                report.readable = False
                return

        report.readable = True
        report.repaired = bool(getattr(doc, "is_repaired", False))
        if report.repaired:
            report.findings.append(Finding(
                "repaired", Risk.LOW, "Document required repair to open",
                "MuPDF rebuilt the cross-reference table. The file is "
                "malformed; treat structural claims with caution."))

        report.page_count = doc.page_count
        report.object_count = max(doc.xref_length() - 1, 0)
        report.metadata = self._clean_metadata(doc.metadata or {})
        report.linearized = report.linearized or bool(
            getattr(doc, "is_fast_webaccess", False))

        if report.page_count > self.limits.max_pages:
            report.findings.append(Finding(
                "page_bomb", Risk.MEDIUM,
                f"Page count {report.page_count:,} exceeds limit",
                "Unusually large page count; extraction will be truncated."))

        self._inspect_permissions(doc, report)
        self._inspect_embedded(doc, report)
        self._inspect_objects(doc, report)
        self._inspect_pages(doc, report)

        try:
            report.outline_entries = len(doc.get_toc() or [])
        except Exception:
            pass

    def _inspect_permissions(self, doc, report: InspectionReport) -> None:
        try:
            perm = int(doc.permissions)
        except Exception:
            return
        # PyMuPDF exposes PDF_PERM_* bit flags.
        flags = {
            "print": getattr(pymupdf, "PDF_PERM_PRINT", 1 << 2),
            "modify": getattr(pymupdf, "PDF_PERM_MODIFY", 1 << 3),
            "copy": getattr(pymupdf, "PDF_PERM_COPY", 1 << 4),
            "annotate": getattr(pymupdf, "PDF_PERM_ANNOTATE", 1 << 5),
            "form": getattr(pymupdf, "PDF_PERM_FORM", 1 << 8),
            "accessibility": getattr(pymupdf, "PDF_PERM_ACCESSIBILITY", 1 << 9),
            "assemble": getattr(pymupdf, "PDF_PERM_ASSEMBLE", 1 << 10),
            "print_hq": getattr(pymupdf, "PDF_PERM_PRINT_HQ", 1 << 11),
        }
        report.permissions = {k: bool(perm & v) for k, v in flags.items()}
        # An unrestricted document reports every bit set. Any cleared bit
        # means the owner imposed a restriction — this is the correct
        # trigger, not `encrypted`, which is False for owner-password files.
        report.permissions_restricted = not all(report.permissions.values())

        if not report.permissions.get("copy", True):
            report.findings.append(Finding(
                "copy_restricted", Risk.INFO, "Text copying is restricted",
                "The document owner has disallowed extraction. This tool can "
                "technically bypass it; respecting it is a legal and policy "
                "decision, not a technical one. See --respect-permissions."))
        if not report.permissions.get("accessibility", True):
            report.findings.append(Finding(
                "a11y_blocked", Risk.MEDIUM,
                "Accessibility extraction is disallowed",
                "The document blocks screen-reader extraction. This is a "
                "WCAG / accessibility-law problem for anything client-facing."))
        if not report.permissions.get("modify", True):
            report.findings.append(Finding(
                "modify_restricted", Risk.INFO, "Modification is restricted",
                "The document is marked read-only by its owner."))

    def _inspect_embedded(self, doc, report: InspectionReport) -> None:
        try:
            count = doc.embfile_count()
        except Exception:
            return
        report.embedded_file_count = count
        if not count:
            return

        total = 0
        for i in range(count):
            try:
                info = doc.embfile_info(i)
            except Exception:
                continue
            name = info.get("filename") or info.get("name") or f"embedded_{i}"
            length = int(info.get("length", 0) or 0)
            total += length
            entry = {
                "index": i, "name": name, "length": length,
                "size_compressed": info.get("size", None),
                "description": info.get("desc", ""),
            }
            report.embedded_files.append(entry)

            ext = Path(str(name)).suffix.lower()
            if ext in {".exe", ".dll", ".scr", ".js", ".vbs", ".ps1", ".bat",
                       ".cmd", ".jar", ".lnk", ".hta", ".msi", ".com", ".pif"}:
                report.findings.append(Finding(
                    "dangerous_attachment", Risk.CRITICAL,
                    f"Executable attachment: {name}",
                    "An embedded executable in a PDF is almost never "
                    "legitimate. Do not detonate.", evidence=[str(name)]))
            elif ext in {".zip", ".rar", ".7z", ".iso", ".img", ".cab"}:
                report.findings.append(Finding(
                    "archive_attachment", Risk.HIGH,
                    f"Archive attachment: {name}",
                    "Archives inside PDFs are a common way to smuggle payloads "
                    "past mail filters.", evidence=[str(name)]))

        if total > self.limits.max_embedded_bytes:
            report.findings.append(Finding(
                "embedded_oversize", Risk.MEDIUM,
                "Embedded payload exceeds limit",
                f"{total:,} bytes of attachments."))

    def _inspect_objects(self, doc, report: InspectionReport) -> None:
        """
        Walk raw object source. This is the layer that catches active content
        the convenience API abstracts away — including objects hidden inside
        compressed object streams.
        """
        hits: Dict[str, Finding] = {}
        urls: Set[str] = set()
        n = doc.xref_length()

        for xref in range(1, min(n, 200_000)):
            try:
                src = doc.xref_object(xref, compressed=True)
            except Exception:
                continue
            if not src:
                continue

            for key, code, risk, detail in _ACTIVE_KEYS:
                if key in src:
                    f = hits.get(code)
                    if f is None:
                        hits[code] = Finding(
                            code, risk, f"{key} present", detail,
                            evidence=[f"xref {xref}"])
                    else:
                        f.count += 1
                        if len(f.evidence) < 8:
                            f.evidence.append(f"xref {xref}")

            if "://" in src:
                for m in _URL_RE.finditer(src.encode("utf-8", "replace")):
                    urls.add(m.group(0).decode("utf-8", "replace"))

        report.findings.extend(hits.values())
        report.urls = sorted(urls)[:500]

        for u in report.urls:
            host = re.sub(r"^\w+://", "", u).split("/")[0].split(":")[0]
            if _PRIVATE_HOST_RE.match(host):
                report.findings.append(Finding(
                    "internal_url", Risk.MEDIUM,
                    "Link to private/internal address",
                    "Links to RFC1918 or loopback addresses can be used for "
                    "SSRF or internal reconnaissance when auto-fetched.",
                    evidence=[u]))
                break
        if any(u.startswith("file://") for u in report.urls):
            report.findings.append(Finding(
                "file_url", Risk.HIGH, "file:// URL present",
                "Attempts to reference the local filesystem.",
                evidence=[u for u in report.urls if u.startswith("file://")][:5]))

    def _inspect_pages(self, doc, report: InspectionReport) -> None:
        text_chars = 0
        images = 0
        annots = 0
        widgets = 0
        fonts: Set[str] = set()
        scan_pages = min(doc.page_count, self.limits.max_pages)

        for i in range(scan_pages):
            try:
                page = doc[i]
            except Exception:
                continue
            try:
                text_chars += len(page.get_text("text") or "")
            except Exception:
                pass
            try:
                images += len(page.get_images(full=True))
            except Exception:
                pass
            try:
                annots += sum(1 for _ in page.annots())
            except Exception:
                pass
            try:
                widgets += sum(1 for _ in page.widgets())
            except Exception:
                pass
            try:
                for f in page.get_fonts(full=True):
                    if len(f) > 3 and f[3]:
                        fonts.add(str(f[3]))
            except Exception:
                pass

        report.image_count = images
        report.annotations = annots
        report.form_fields = widgets
        report.fonts = sorted(fonts)[:200]
        report.has_text = text_chars > 0

        # A page-heavy document with almost no text is a scan. Callers need
        # to know this before concluding "the PDF has no content" — the
        # content is there, it just needs OCR.
        if scan_pages > 0:
            per_page = text_chars / scan_pages
            report.likely_scanned = per_page < 50 and images > 0
            if report.likely_scanned:
                report.findings.append(Finding(
                    "likely_scanned", Risk.INFO, "Likely a scanned document",
                    f"~{per_page:.0f} chars/page with {images} images. Text "
                    "extraction will return little; OCR is required."))

        if widgets:
            report.findings.append(Finding(
                "has_form", Risk.INFO, f"{widgets} form field(s)",
                "Interactive form. Check /SubmitForm targets before filling."))

    # ─── Helpers ───

    @staticmethod
    def _sha256(p: Path, chunk: int = 1 << 20) -> str:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for block in iter(lambda: f.read(chunk), b""):
                h.update(block)
        return h.hexdigest()

    @staticmethod
    def _clean_metadata(md: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in md.items()
                if v not in (None, "", b"") and not k.startswith("_")}


# ═══════════════════════════════════════════════════════════════
# Extraction
# ═══════════════════════════════════════════════════════════════

@dataclass
class PageContent:
    number: int                      # 1-based, matches what a human sees
    text: str = ""
    char_count: int = 0
    word_count: int = 0
    image_count: int = 0
    table_count: int = 0
    links: List[str] = field(default_factory=list)
    rotation: int = 0
    width: float = 0.0
    height: float = 0.0
    truncated: bool = False
    ocr: bool = False                     # text produced by OCR, not the PDF


@dataclass
class ExtractionResult:
    path: str
    filename: str
    sha256: str
    page_count: int = 0
    pages: List[PageContent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    outline: List[Dict[str, Any]] = field(default_factory=list)
    form_data: Dict[str, Any] = field(default_factory=dict)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)

    written_files: List[str] = field(default_factory=list)
    truncated: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    inspection: Optional[Dict[str, Any]] = None
    extracted_at: str = field(default_factory=_now)
    ocr_pages: int = 0
    ocr_available: bool = False

    @property
    def text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)

    @property
    def char_count(self) -> int:
        return sum(p.char_count for p in self.pages)

    def to_dict(self, include_text: bool = True) -> Dict[str, Any]:
        d = asdict(self)
        if not include_text:
            for p in d["pages"]:
                p.pop("text", None)
        d["char_count"] = self.char_count
        return d


class PDFExtractor:
    """
    Content extraction with a safety interlock.

    `extract()` inspects first and refuses HIGH/CRITICAL documents unless
    `force=True`. This is the opposite of most libraries, which happily
    parse anything — the default should be the safe one, because the
    unsafe path is the one people reach for at 2am during an incident.
    """

    def __init__(self, limits: Optional[Limits] = None,
                 inspector: Optional[PDFInspector] = None):
        self.limits = limits or Limits()
        self.inspector = inspector or PDFInspector(self.limits)

    def extract(
        self,
        path: os.PathLike | str,
        *,
        password: Optional[str] = None,
        pages: Optional[Iterable[int]] = None,     # 1-based
        want_text: bool = True,
        want_tables: bool = False,
        want_images: bool = False,
        want_attachments: bool = False,
        output_dir: Optional[os.PathLike | str] = None,
        force: bool = False,
        respect_permissions: bool = False,
        skip_inspection: bool = False,
        ocr: bool = False,
        ocr_lang: str = "eng",
    ) -> ExtractionResult:
        _require_backend()
        p = Path(path)

        report = None
        if not skip_inspection:
            report = self.inspector.inspect(p, password=password)

        result = ExtractionResult(
            path=str(p.resolve()), filename=p.name,
            sha256=report.sha256 if report else PDFInspector._sha256(p),
            inspection=report.to_dict() if report else None,
        )
        result.ocr_available = _find_tesseract() is not None
        if ocr and not _find_tesseract():
            result.errors.append(
                "ocr requested but tesseract was not found on PATH or in "
                "standard install locations")
            return result

        if report is not None:
            if report.needs_password:
                result.errors.append("password required; supply password=")
                return result
            if not report.safe_to_extract and not force:
                result.errors.append(
                    f"refusing to extract: risk={report.risk.value}. "
                    f"Findings: "
                    + "; ".join(f"{f.code}({f.risk.value})"
                                for f in report.findings
                                if _RISK_ORDER[f.risk] >= _RISK_ORDER[Risk.HIGH])
                    + ". Pass force=True to override.")
                return result
            if (respect_permissions
                    and not report.permissions.get("copy", True)):
                result.errors.append(
                    "document forbids copying and respect_permissions=True")
                return result

        out = Path(output_dir).resolve() if output_dir else None
        if out:
            out.mkdir(parents=True, exist_ok=True)

        try:
            doc = pymupdf.open(str(p))
        except Exception as e:
            result.errors.append(f"open failed: {type(e).__name__}: {e}")
            return result

        try:
            if doc.needs_pass and not doc.authenticate(password or ""):
                result.errors.append("authentication failed")
                return result

            result.page_count = doc.page_count
            result.metadata = PDFInspector._clean_metadata(doc.metadata or {})
            result.outline = self._outline(doc)

            wanted = self._page_indices(doc.page_count, pages, result)
            budget = self.limits.max_text_chars

            for idx in wanted:
                pc = self._extract_page(
                    doc, idx, want_text, want_tables, want_images,
                    budget, out, result, ocr=ocr, ocr_lang=ocr_lang)
                budget -= pc.char_count
                result.pages.append(pc)
                if budget <= 0:
                    result.truncated = True
                    result.warnings.append(
                        f"text budget exhausted after page {pc.number}")
                    break

            if want_attachments:
                self._extract_attachments(doc, out, result)

            if doc.is_form_pdf:
                result.form_data = self._extract_form(doc, result)

        except LimitExceeded as e:
            result.truncated = True
            result.warnings.append(str(e))
        except Exception as e:
            result.errors.append(f"extract failed: {type(e).__name__}: {e}")
        finally:
            doc.close()

        return result

    # ─── Per-page ───

    def _extract_page(self, doc, idx: int, want_text: bool, want_tables: bool,
                      want_images: bool, budget: int,
                      out: Optional[Path], result: ExtractionResult,
                      ocr: bool = False, ocr_lang: str = "eng") -> PageContent:
        page = doc[idx]
        rect = page.rect
        pc = PageContent(number=idx + 1, rotation=page.rotation,
                         width=rect.width, height=rect.height)

        try:
            imgs = page.get_images(full=True)
            pc.image_count = len(imgs)
        except Exception:
            imgs = []

        if want_text:
            try:
                txt = page.get_text("text") or ""
            except Exception as e:
                txt = ""
                result.warnings.append(f"page {idx+1} text: {type(e).__name__}")
            if len(txt) > budget:
                txt = txt[:max(budget, 0)]
                pc.truncated = True
            pc.text = txt
            pc.char_count = len(txt)
            pc.word_count = len(txt.split())

        if ocr and pc.char_count < _OCR_MIN_CHARS and pc.image_count > 0:
            ocr_text = self._ocr_page(page, idx, ocr_lang)
            if ocr_text:
                pc.text = (pc.text + "\n\n" + ocr_text).strip()
                pc.ocr = True
                result.ocr_pages += 1
                pc.char_count = len(pc.text)
                pc.word_count = len(pc.text.split())

        try:
            pc.links = [l["uri"] for l in page.get_links() if l.get("uri")]
        except Exception:
            pass

        if want_images and imgs:
            self._extract_images(doc, page, idx, imgs, out, result)

        if want_tables:
            pc.table_count = self._extract_tables(page, idx, result)

        return pc

    def _ocr_page(self, page, idx: int, lang: str = "eng") -> str:
        """
        Render the page and run Tesseract. Returns '' on any failure — OCR
        is best-effort and must never crash extraction. The render goes
        through a pixel budget so a huge scan cannot blow up memory, and the
        subprocess has a hard timeout so a hung Tesseract cannot stall us.
        """
        exe = _find_tesseract()
        if exe is None:
            return ""

        if self.limits.ocr_timeout_seconds <= 0:
            return ""

        matrix = pymupdf.Matrix(self.limits.ocr_dpi / 72,
                                self.limits.ocr_dpi / 72)
        try:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
        except Exception as e:
            return ""

        if pix.width * pix.height > self.limits.max_image_pixels:
            return ""

        try:
            png = pix.tobytes("png")
        except Exception:
            return ""

        tmp = None
        try:
            with tempfile.NamedTemporaryFile(
                    suffix=".png", prefix="pdftool_ocr_", delete=False) as f:
                f.write(png)
                tmp = f.name
            proc = subprocess.run(
                [exe, tmp, "stdout", "--psm", "6", "-l", lang],
                capture_output=True, timeout=self.limits.ocr_timeout_seconds)
        except subprocess.TimeoutExpired:
            return ""
        except Exception:
            return ""
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

        if proc.returncode != 0:
            return ""
        try:
            return proc.stdout.decode("utf-8", "replace").strip()
        except Exception:
            return ""

    def _extract_images(self, doc, page, idx: int, imgs, out: Optional[Path],
                        result: ExtractionResult) -> None:
        for i, info in enumerate(imgs):
            if len(result.images) >= self.limits.max_images:
                result.truncated = True
                result.warnings.append("image limit reached")
                return
            xref = info[0]
            try:
                raw = doc.extract_image(xref)
            except Exception as e:
                result.warnings.append(
                    f"page {idx+1} image {i}: {type(e).__name__}")
                continue

            w, h = raw.get("width", 0), raw.get("height", 0)
            # Guard the classic decompression bomb: small compressed stream,
            # enormous pixel surface.
            if w * h > self.limits.max_image_pixels:
                result.warnings.append(
                    f"page {idx+1} image {i}: {w}x{h} exceeds pixel limit; skipped")
                continue

            entry = {
                "page": idx + 1, "index": i, "xref": xref,
                "width": w, "height": h,
                "ext": raw.get("ext", "bin"),
                "colorspace": raw.get("colorspace", None),
                "bytes": len(raw.get("image", b"")),
                "sha256": hashlib.sha256(raw.get("image", b"")).hexdigest(),
            }
            if out:
                name = f"p{idx+1:04d}_img{i:03d}.{entry['ext']}"
                fp = out / name
                fp.write_bytes(raw["image"])
                entry["file"] = str(fp)
                result.written_files.append(str(fp))
            result.images.append(entry)

    def _extract_tables(self, page, idx: int, result: ExtractionResult) -> int:
        if not hasattr(page, "find_tables"):
            result.warnings.append("table extraction unavailable in this backend")
            return 0

        # Two-line strategy ladder. `lines` latches onto ruling lines/vector
        # graphics and is precise; `text` infers tables from text alignment
        # alone and catches the borderless grids `lines` misses. Running both
        # and merging produces duplicates, so mirror the PyMuPDF REPL habit
        # and only climb the ladder when the strict pass came up empty.
        strategies = ["lines", "text"]
        for strat in strategies:
            found = None
            try:
                with _silenced_stdout():
                    found = page.find_tables(strategy=strat)
            except Exception as e:
                result.warnings.append(
                    f"page {idx+1} tables ({strat}): {type(e).__name__}")
                continue
            tables = list(getattr(found, "tables", []) or [])
            if not tables:
                continue
            for t_i, t in enumerate(tables):
                try:
                    rows = t.extract()
                except Exception:
                    continue
                result.tables.append({
                    "page": idx + 1, "index": t_i,
                    "rows": len(rows), "cols": len(rows[0]) if rows else 0,
                    "strategy": strat,
                    "header_found": bool(t.header is not None),
                    "data": rows,
                })
            return len(tables)
        return 0

    # ─── Document-level ───

    def _extract_attachments(self, doc, out: Optional[Path],
                             result: ExtractionResult) -> None:
        try:
            n = doc.embfile_count()
        except Exception:
            return
        total = 0
        for i in range(n):
            try:
                info = doc.embfile_info(i)
                data = doc.embfile_get(i)
            except Exception as e:
                result.warnings.append(f"attachment {i}: {type(e).__name__}")
                continue
            total += len(data)
            if total > self.limits.max_embedded_bytes:
                result.warnings.append("attachment budget exceeded; stopping")
                result.truncated = True
                return

            name = str(info.get("filename") or f"attachment_{i}")
            entry = {
                "index": i, "name": name, "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            if out:
                # Attachment names come from untrusted input: strip any path
                # component so a crafted "..\..\startup\evil.exe" cannot
                # escape the output directory.
                safe = Path(name).name or f"attachment_{i}"
                safe = re.sub(r"[^A-Za-z0-9._-]", "_", safe)[:120]
                fp = out / f"attach_{i:03d}_{safe}"
                fp.write_bytes(data)
                entry["file"] = str(fp)
                result.written_files.append(str(fp))
            result.attachments.append(entry)

    def _extract_form(self, doc, result: ExtractionResult) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        try:
            for page in doc:
                for w in page.widgets():
                    if w.field_name:
                        data[w.field_name] = {
                            "value": w.field_value,
                            "type": w.field_type_string,
                            "page": page.number + 1,
                        }
        except Exception as e:
            result.warnings.append(f"form: {type(e).__name__}")
        return data

    @staticmethod
    def _outline(doc) -> List[Dict[str, Any]]:
        try:
            return [{"level": lvl, "title": title, "page": pg}
                    for lvl, title, pg in (doc.get_toc() or [])]
        except Exception:
            return []

    def _page_indices(self, total: int, pages: Optional[Iterable[int]],
                      result: ExtractionResult) -> List[int]:
        if pages is None:
            sel = list(range(min(total, self.limits.max_pages)))
            if total > self.limits.max_pages:
                result.truncated = True
                result.warnings.append(
                    f"page limit {self.limits.max_pages} < {total}")
            return sel
        out = []
        for n in pages:
            i = int(n) - 1
            if 0 <= i < total:
                out.append(i)
            else:
                result.warnings.append(f"page {n} out of range 1..{total}")
        return out


# ═══════════════════════════════════════════════════════════════
# Page-range parsing
# ═══════════════════════════════════════════════════════════════

def parse_page_spec(spec: str) -> List[int]:
    """'1,3,5-8,12' -> [1,3,5,6,7,8,12]. 1-based, deduped, ordered."""
    out: Set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            # Split on every hyphen, not just the first: "1--2" must be
            # rejected outright rather than silently read as 1..-2 and
            # normalised into a reversed range.
            bits = part.split("-")
            if len(bits) != 2 or not all(b.strip().isdigit() for b in bits):
                raise ValueError(f"bad page range: {part!r}")
            lo, hi = int(bits[0]), int(bits[1])
            if lo > hi:
                lo, hi = hi, lo
            if hi - lo > 100_000:
                raise ValueError(f"page range too large: {part!r}")
            out.update(range(lo, hi + 1))
        else:
            try:
                out.add(int(part))
            except ValueError:
                raise ValueError(f"bad page number: {part!r}")
    return sorted(n for n in out if n > 0)


# ═══════════════════════════════════════════════════════════════
# Convenience API
# ═══════════════════════════════════════════════════════════════

def inspect_pdf(path, password: Optional[str] = None,
                limits: Optional[Limits] = None) -> InspectionReport:
    return PDFInspector(limits).inspect(path, password=password)


def extract_pdf(path, **kwargs) -> ExtractionResult:
    limits = kwargs.pop("limits", None)
    return PDFExtractor(limits).extract(path, **kwargs)


def extract_text(path, password: Optional[str] = None,
                 force: bool = False, ocr: bool = False,
                 ocr_lang: str = "eng") -> str:
    """Text only. Returns '' rather than raising when extraction is refused."""
    r = extract_pdf(path, password=password, force=force,
                    want_text=True, ocr=ocr, ocr_lang=ocr_lang)
    return r.text


def scan_directory(root, recursive: bool = True,
                   limits: Optional[Limits] = None) -> List[InspectionReport]:
    """Triage a folder of PDFs. Sorted most dangerous first."""
    rootp = Path(root)
    pattern = "**/*.pdf" if recursive else "*.pdf"
    insp = PDFInspector(limits)
    reports: List[InspectionReport] = []
    for f in sorted(rootp.glob(pattern)):
        try:
            reports.append(insp.inspect(f))
        except Exception as e:
            r = InspectionReport(path=str(f), filename=f.name,
                                 size_bytes=f.stat().st_size if f.exists() else 0,
                                 sha256="")
            r.errors.append(f"{type(e).__name__}: {e}")
            reports.append(r)
    reports.sort(key=lambda r: -_RISK_ORDER[r.risk])
    return reports
