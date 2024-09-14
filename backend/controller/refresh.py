import chromadb

chroma_client = chromadb.PersistentClient('./db/')
chroma_client.delete_collection(name='image_vectors')
