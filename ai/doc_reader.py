import os
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file_path: str) -> str:
    """
    Turns an uploaded file into plain text.
    Unsupported files return empty text instead of crashing.
    Supports .txt, .pdf, .docx.
    """
    if not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        elif ext == '.pdf':
            import PyPDF2
            text = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)
            
        elif ext == '.docx':
            import docx
            doc = docx.Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
            
        else:
            logger.warning(f"Unsupported file extension: {ext}")
            return ""
            
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""
