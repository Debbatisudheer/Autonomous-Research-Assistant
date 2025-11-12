# pdf_to_text.py

from pypdf import PdfReader

def pdf_to_text(pdf_path: str) -> str:
    """
    Extract text from a PDF file and return as one string.
    """
    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"

    return text
