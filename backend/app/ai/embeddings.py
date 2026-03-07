from sentence_transformers import SentenceTransformer
from functools import lru_cache

@lru_cache(maxsize=1)
def get_model():
    print("Loading Embedding model ...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Embedding model loaded successfully")
    return model


def embed_text(text : str):
    model = get_model()
    return model.encode(text, show_progress_bar=False).tolist()
