"""Per-format injectors (PPTX, DOCX, XLSX)."""

from common_file_generator.injectors.docx import DocxInjector
from common_file_generator.injectors.pptx import PptxInjector
from common_file_generator.injectors.xlsx import XlsxInjector

__all__ = ["DocxInjector", "PptxInjector", "XlsxInjector"]
