from io import BytesIO
import chromadb
import torch
from PIL import Image
from joblib import load
from controller.textProcessingController import TextProcessing
import os
import clip


# Configure ChromaDB


class ImageSearcher:
    def __init__(self):
        controller_folder = 'controller'
        model_path = os.path.join(controller_folder, 'image-text-searcher-v-3.joblib')
        preprocessor_path = os.path.join(controller_folder, 'preprocessor-v-3.joblib')
        model = load(model_path)
        self.model = model.eval()
        self.preprocessor = load(preprocessor_path)
        self.chroma_client = chromadb.PersistentClient('./controller/db/')
        self.images = self.chroma_client.get_or_create_collection(name='image_vectors',
                                                                  metadata={"hnsw:space": "cosine"}
                                                                  )
        self.TextProcessing = TextProcessing()

    def seed_one_image(self, image_uri, image_data, image_format, image_date):
        try:
            with Image.open(BytesIO(image_data)) as img:
                try:
                    image_input = self.preprocessor(img).unsqueeze(0).to('cpu')

                    with torch.no_grad():
                        embedding = self.model.encode_image(image_input).cpu().numpy()

                    # Print the dimensions of the embeddings
                    print(f"Embedding dimensions for {image_uri}: {embedding.shape}")

                    embedding_list = embedding.tolist()
                    metadata = {
                        "image_date": image_date,
                        "type": image_format,
                    }

                    ids = image_uri
                    self.images.upsert(
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
                results = self.images.get(where={"image_date": {
                    "$eq": date_search
                }})
                print(results)
                if len(results['ids']) == 0:
                    return None
                return results['ids']
            else:
                return None
        # if len(tokens) == 0:
        #     print(f"Not an english word:", query)
        #     return None
        # for token in tokens:
        #     if not self.TextProcessing.check_word(token):
        #         print(f"Not an english word:", token)
        #         return None
        try:
            text_input = clip.tokenize([query]).to('cpu')
            with torch.no_grad():
                embedding = self.model.encode_text(text_input).cpu().numpy()

            text_emb = embedding.tolist()
            results = self.images.query(
                query_embeddings=text_emb,
                n_results=5,
            )

            print(results)
            if results and results['ids']:
                return results['ids'][0]
            else:
                return None

        except Exception as e:
            print(f"Text embedding or query failed: {e}")
            return None

    def get_inserted_images(self):
        return self.images.get()
