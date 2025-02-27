import PyPDF2
import docx

def extract_text(file):
    """
    Extracts text from PDF, DOCX, or TXT files.
    """
    try:
        if file.filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            return "".join([page.extract_text() or "" for page in reader.pages])
        elif file.filename.endswith('.docx'):
            doc = docx.Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        elif file.filename.endswith('.txt'):
            return file.read().decode('utf-8')
        else:
            return ""
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""
