
from src.rag.document_loader import load_documents
from src.rag.chunking import chunk_documents
from src.rag.vector_store import VectorStore


def main():

    print("Loading PDF documents...")

    documents = load_documents()

    print(f"Loaded documents/pages: {len(documents)}")

    print("Creating document chunks...")

    chunks = chunk_documents(documents)

    print(f"Total chunks: {len(chunks)}")

    print("Building persistent ChromaDB collection...")

    vector_store = VectorStore()
    vector_store.build(chunks)

    print("ChromaDB indexing completed successfully.")


if __name__ == "__main__":
    main()
