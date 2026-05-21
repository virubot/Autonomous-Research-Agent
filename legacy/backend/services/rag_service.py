from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class RAG:
    def __init__(self):
        # 🔥 LOAD EMBEDDING MODEL
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.documents = []
        self.vectors = None

    def add_documents(self, docs):
        self.documents = docs

        # 🔥 CREATE EMBEDDINGS
        self.vectors = self.model.encode(docs)

    def query(self, query, k=5):
        if not self.documents or self.vectors is None:
            return []

        # 🔥 QUERY EMBEDDING
        query_vec = self.model.encode([query])

        # 🔥 SIMILARITY
        scores = cosine_similarity(query_vec, self.vectors)[0]

        # 🔥 TOP K RESULTS
        top_k_idx = scores.argsort()[-k:][::-1]

        return [self.documents[i] for i in top_k_idx]