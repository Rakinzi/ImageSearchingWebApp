import os
from controller.searchController import ImageSearcher


class ImageProcessor(ImageSearcher):

    def __init__(self, file_data=None, image_details=None, data=None):
        super().__init__()
        self.file_data = file_data
        self.image_details = image_details
        self.data = data

    def process_images(self):
        print(self.image_details)
        if not self.file_data or not self.image_details:
            message = "This is not an image"
            images = None
            return message, images, 0
        image_format = self.image_details.get('filename').split('.')[1]
        image_date = self.image_details.get('creationDate')
        filename = self.image_details.get('filename', 'image')
        image_path = os.path.join('static/uploads/images', filename)

        print(image_path)
        with open(image_path, 'wb') as f:
            print("Saving File")
            f.write(self.file_data)

        processor = super().seed_one_image(
            image_uri=image_path,
            image_data=self.file_data,
            image_format=image_format,
            image_date=image_date,
        )

        if processor != 0:
            images_ids = super().get_inserted_images()['ids']
            print("Image Processed", image_path)
            return "Image processed successfully", images_ids, 1
        else:
            return "Error inserting image", None, 0

    def search_images(self):
        if 'query' in self.data:
            query = self.data['query']
            images = super().search_one_image(query=query)
            if images is None:
                message = "No Images Matches your query"
                images = None
                return message, images, 0
            message = "Images Returned"
            images = None
            return message, images, 1
        else:
            message = "The key query is not found in your data"
            images = None
            return message, images, 0
