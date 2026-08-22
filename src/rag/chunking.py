def chunk_documents(documents, chunk_size=500, overlap=100):
    """
    Split document text into overlapping chunks
    while preserving the original metadata.
    """

    chunks = []

    for document in documents:
        text = document["text"]

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end]

            chunk = {
                **document,
                "text": chunk_text
            }

            chunks.append(chunk)

            start += chunk_size - overlap

    return chunks