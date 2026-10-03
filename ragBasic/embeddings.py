from numpy import dot
from numpy.linalg import norm
from sentence_transformers import SentenceTransformer


def cosine_similarity(vec1, vec2):
    return dot(vec1, vec2) / (norm(vec1) * norm(vec2))  # cosine


model = SentenceTransformer("all-MiniLM-L6-v2")  # ① free, fast, 384 dims

vec = model.encode("Ruby cat is sleeping on the sofa.")  # ② encode a sentence to vector
print(vec.shape)  # → (384,)  — 384 numbers
print(vec[:5])  # → [-0.05, 0.12, 0.41, -0.08, 0.22] (something like that)

v1 = model.encode("A cat is sleeping on the couch")
v2 = model.encode("A kitten is napping on the sofa")
print(cosine_similarity(v1, v2))  # → 0.760522
