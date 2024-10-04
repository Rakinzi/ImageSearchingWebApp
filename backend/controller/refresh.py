import chromadb

chroma_client = chromadb.PersistentClient('./db/')
images = chroma_client.delete_collection(name='image_vectors')