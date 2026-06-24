"""Per-format injectors (PPTX, DOCX, XLSX)."""

from ms_office_file_generator.injectors.docx import DocxInjector
from ms_office_file_generator.injectors.pptx import PptxInjector
from ms_office_file_generator.injectors.xlsx import XlsxInjector

__all__ = ["DocxInjector", "PptxInjector", "XlsxInjector"]
