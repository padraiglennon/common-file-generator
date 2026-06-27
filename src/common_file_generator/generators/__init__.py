"""Generate mode: build complex files from scratch (not template-driven).

Where injectors fill a Golden template, generators *create* a document at a
chosen complexity level - the common "give me an N-slide complex deck" case.
"""

from common_file_generator.generators.docx import DocxComplexityGenerator
from common_file_generator.generators.markdown import MarkdownComplexityGenerator
from common_file_generator.generators.pdf import PdfComplexityGenerator
from common_file_generator.generators.pptx import PptxComplexityGenerator
from common_file_generator.generators.xlsx import XlsxComplexityGenerator

__all__ = [
    "DocxComplexityGenerator",
    "MarkdownComplexityGenerator",
    "PdfComplexityGenerator",
    "PptxComplexityGenerator",
    "XlsxComplexityGenerator",
]
