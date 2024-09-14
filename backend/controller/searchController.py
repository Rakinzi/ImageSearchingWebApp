from io import BytesIO
import chromadb
from PIL import Image
from joblib import load
from controller.textProcessingController import TextProcessing

chroma_client = chromadb.PersistentClient('../controller/db/')
images = chroma_client.get_or_create_collection(name='image_vectors', metadata={"hnsw:space": "cosine"})


class ImageSearcher:
    def __init__(self):
        self.model = load('controller/image-text-searcher-v-2.joblib')
        self.TextProcessing = TextProcessing()

    def seed_one_image(self, image_uri, image_data, image_format, image_date):
        model = self.model
        try:
            with Image.open(BytesIO(image_data)) as img:
                try:
                    embedding = model.encode(img)
                    embedding_list = embedding.tolist()
                    metadata = {
                        "image_date": image_date,
                        "type": image_format,
                    }
                    ids = image_uri
                    images.upsert(
                        embeddings=embedding_list,
                        ids=ids,
                        metadatas=metadata
                    )
                    print('Embeddings Created')
                    return 1
                except Exception as embed_error:
                    print(f"Embedding failed for {image_uri}: {embed_error}")
                    return 0
        except Exception as img_open_error:
            print(f"Failed to open image {image_uri}: {img_open_error}")
            return 0

    def search_one_image(self, query):
        tokens = self.TextProcessing.text_processing_model(query)
        if self.TextProcessing.date_processor(query):
            date_search = self.TextProcessing.date_parser(query)
            if date_search:
                print(
                    date_search
                )
                results = images.get(where={"image_date": {
                    "$eq": date_search
                }})
                print(results)
                if len(results['ids']) == 0:
                    return None
                return results['ids']
            else:
                return None
        if len(tokens) == 0:
            print(f"Not an english word:", query)
            return None
        for token in tokens:
            if not self.TextProcessing.check_word(token):
                print(f"Not an english word:", token)
                return None
        model = self.model
        text_emb = model.encode(query).tolist()
        results = images.query(
            query_embeddings=text_emb,
            n_results=5,
        )
        print(results)
        return results['ids'][0]

    @staticmethod
    def get_inserted_images():
        return images.get()
