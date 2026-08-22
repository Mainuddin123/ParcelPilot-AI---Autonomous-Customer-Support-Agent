from pypdf import PdfReader

from src.config import DOCUMENTS_DIR, DOCUMENT_METADATA


def load_documents():
    """
    Extract text from all PDF documents and attach metadata.
    """

    documents = []

    for filename, metadata in DOCUMENT_METADATA.items():
        file_path = DOCUMENTS_DIR / filename

        if not file_path.exists():
            print(f"Warning: {filename} not found.")
            continue

        reader = PdfReader(file_path)

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                document = {
                    "text": text,
                    "source": filename,
                    "page": page_number,
                    **metadata
                }

                documents.append(document)

    return documents