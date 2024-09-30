import chromadb

# chroma_client = chromadb.PersistentClient('../chroma_db/')
# images = chroma_client.delete_collection(name='face_collection')

chroma_client = chromadb.PersistentClient('./db/')
images = chroma_client.delete_collection(name='image_vectors')