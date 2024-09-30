from io import BytesIO
import chromadb
import torch
from PIL import Image
from joblib import load
from controller.textProcessingController import TextProcessing
import os
import clip
import exifread
from geopy.geocoders import Nominatim


# Configure ChromaDB


class ImageSearcher:
    def __init__(self):
        controller_folder = 'controller'
        model_path = os.path.join(controller_folder, 'image-text-searcher-v-3.joblib')
        preprocessor_path = os.path.join(controller_folder, 'preprocessor-v-3.joblib')
        print(model_path)
        model = load(model_path)
        self.model = model.eval()
        self.preprocessor = load(preprocessor_path)
        self.chroma_client = chromadb.PersistentClient('./controller/db/')
        self.images = self.chroma_client.get_or_create_collection(name='image_vectors',
                                                                  metadata={"hnsw:space": "cosine"}
                                                                  )
        self.TextProcessing = TextProcessing()

    def seed_one_image(self, image_uri, image_data, image_format, image_date, image_details):
        geolocator = Nominatim(user_agent="geoapiExercises")
        crucial_tags = [
            'EXIF ImageWidth',
            'EXIF ImageLength',
            'Image Make',
            'Image Model',
            'EXIF DateTimeOriginal',
            'EXIF DateTimeDigitized',
            'GPS GPSLatitude',  # Add GPS latitude
            'GPS GPSLongitude',  # Add GPS longitude
        ]

        image_data_processed = BytesIO(image_data)
        exif_data = exifread.process_file(image_data_processed, details=False)

        print(f"EXIF data for {image_uri}: {exif_data}")
        if exif_data:
            exif = {}
            latitude = None
            longitude = None

            for tag in crucial_tags:
                if tag in exif_data:
                    exif[tag] = str(exif_data[tag])  # Store the EXIF tag and its value as a string
                    # Extract GPS coordinates if available
                    if tag == 'GPS GPSLatitude':
                        latitude = str(exif_data[tag])
                    elif tag == 'GPS GPSLongitude':
                        longitude = str(exif_data[tag])

            image_details.update(exif)

            # Step 4: Reverse geocode if both latitude and longitude are available
            if latitude and longitude:
                try:
                    location = geolocator.reverse(f"{latitude}, {longitude}")
                    if location:
                        image_details['location'] = location.address  # Add location to image details
                except Exception as e:
                    image_details['location'] = None

        try:
            with Image.open(BytesIO(image_data)) as img:
                try:

                    img.thumbnail((128, 128))
                    thumbnail_io = BytesIO()
                    img.save(thumbnail_io, format='JPEG')  # Save the thumbnail as JPEG to a BytesIO object
                    thumbnail_io.seek(0)

                    thumbnail_path = os.path.join('static/uploads/thumbnails', f"thumb_{image_details['filename']}")

                    with open(thumbnail_path, 'wb') as f:
                        f.write(thumbnail_io.read())

                    print("Images saved")
                    image_details['thumbnail'] = thumbnail_path
                    if image_details['thumbnail'] is not None:
                        try:
                            image_input = self.preprocessor(img).unsqueeze(0).to('cpu')

                            with torch.no_grad():
                                embedding = self.model.encode_image(image_input).cpu().numpy()

                            # Print the dimensions of the embeddings
                            print(f"Embedding dimensions for {image_uri}: {embedding.shape}")

                            embedding_list = embedding.tolist()

                            image_details['image_date'] = image_date
                            image_details['type'] = image_format

                            ids = image_uri
                            self.images.upsert(
                                embeddings=embedding_list,
                                ids=ids,
                                metadatas=image_details
                            )
                            print('Embeddings Created')
                            return 1
                        except Exception as e:
                            print(f"Failed to make embedding for {e}")
                            return 0
                except Exception as e:
                    print(f"{e}")
                    image_details['thumbnail'] = None
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
                images =  results['ids'][0]
                normalized_images = [os.path.normpath(image) for image in images]
                return normalized_images
            else:
                return None

        except Exception as e:
            print(f"Text embedding or query failed: {e}")
            return None

    def get_inserted_images(self):
        return self.images.get()
