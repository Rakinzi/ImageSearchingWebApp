import chromadb

chroma_client = chromadb.PersistentClient('./db/')
images = chroma_client.get_collection(name='image_vectors')
print(images.get())