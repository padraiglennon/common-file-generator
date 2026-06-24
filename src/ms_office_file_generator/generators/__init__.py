"""Generate mode: build complex Office files from scratch (not template-driven).

Where injectors fill a Golden template, generators *create* a document at a
chosen complexity level - the common "give me an N-slide complex deck" case.
"""

from ms_office_file_generator.generators.docx import DocxComplexityGenerator
from ms_office_file_generator.generators.markdown import MarkdownComplexityGenerator
from ms_office_file_generator.generators.pdf import PdfComplexityGenerator
from ms_office_file_generator.generators.pptx import PptxComplexityGenerator
from ms_office_file_generator.generators.xlsx import XlsxComplexityGenerator

__all__ = [
    "DocxComplexityGenerator",
    "MarkdownComplexityGenerator",
    "PdfComplexityGenerator",
    "PptxComplexityGenerator",
    "XlsxComplexityGenerator",
]
