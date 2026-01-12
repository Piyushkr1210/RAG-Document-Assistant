import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# Tunable confidence threshold
# Lower = stricter, Higher = looser
MAX_DISTANCE_THRESHOLD = 1.5  

def retrieve(query, index, texts, data, k=3):
    """
    Retrieves top-k relevant evidence chunks using semantic similarity.
    Filters out low-confidence matches to prevent hallucination.
    """

    if index.ntotal == 0:
        return []

    # 1️⃣ Embed query
    q_embedding = model.encode([query])

    # 2️⃣ Search FAISS
    distances, indices = index.search(
        np.array(q_embedding).astype("float32"), k
    )

    results = []

    # 3️⃣ Confidence filtering
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue

        # Reject weak matches
        if dist > MAX_DISTANCE_THRESHOLD:
            print(f"Low confidence match ignored: {dist}")
            continue

        results.append(data[idx])

    return results
