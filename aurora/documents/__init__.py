"""
AGENCY OS — Document processing.

PDF tooling lives here and is imported lazily. `pdftool` depends on PyMuPDF
(AGPL-3.0); keeping the import out of this package's __init__ means the
dependency is only pulled in when a caller actually asks for it, and the
whole AGPL surface can be removed by deleting one file.
"""

__all__ = ["pdftool"]
