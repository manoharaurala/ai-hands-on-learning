from numpy import dot
from numpy.linalg import norm
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")   # ① free, fast, 384 dims

vec = model.encode("A cat is sleeping on the couch")  # ② that's an embedding!
print("First vector shape:", vec.shape)  # → (384,) — 384 numbers
print("First vector:", vec)

v1 = model.encode("A cat is sleeping on the couch")
v2 = model.encode("A kitten is napping on the sofa")
print("\nVector 1 (first 5 dimensions):", v1[:5])
print("Vector 2 (first 5 dimensions):", v2[:5])

# Cosine similarity measures the angle between two vectors:
#   cosine_similarity = (v1 · v2) / (||v1|| × ||v2||)
# `dot(v1, v2)` is the dot product, and `norm(...)` is each vector's length.
similarity = dot(v1, v2) / (norm(v1) * norm(v2))
print(similarity)       # → 0.87 (very similar 🎉)