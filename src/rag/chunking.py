
def chunk_documents(documents, chunk_size=500, overlap=100):
    """
    Split document text into overlapping chunks
    while preserving original metadata.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    chunks = []
    step = chunk_size - overlap

    for document in documents:
        text = document.get("text", "")

        if not text.strip():
            continue

        for start in range(0, len(text), step):
            chunk_text = text[start:start + chunk_size]

            if not chunk_text.strip():
                continue

            chunk = {
                **document,
                "text": chunk_text
            }

            chunks.append(chunk)

    return chunks
