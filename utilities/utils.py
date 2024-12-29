from PyPDF2 import PdfReader

def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text
    except Exception as e:
        raise ValueError(f"Error processing PDF: {str(e)}")