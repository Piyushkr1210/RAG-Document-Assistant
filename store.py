from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_store(data):
    if not data:
        raise ValueError(
            "❌ No documents ingested.\n"
            "➡️ Add PDFs to data/docs or images to data/images."
        )

    texts = [d["content"] for d in data]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    )

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))

    return index, texts, data
