from imutils import paths
import face_recognition
import pickle
import cv2
import os

# Convert relative path to absolute path
image_folder = os.path.abspath('../static/uploads/images/')
imagePaths = list(paths.list_images(image_folder))
knownEncodings = []
knownNames = []

# Loop over the image paths
for (i, imagePath) in enumerate(imagePaths):
    print(f"Processing image: {imagePath}")

    # Split the imagePath
    parts = imagePath.split(os.path.sep)
    print(f"Path parts: {parts}")

    if len(parts) < 2:
        print(f"Skipping file {imagePath} due to unexpected path format.")
        continue

    name = parts[-2]
    print(f"Extracted name: {name}")
    # Rest of your processing logic

    # Load the input image and convert it from BGR (OpenCV ordering) to RGB
    image = cv2.imread(imagePath)
    if image is None:
        print(f"Failed to load image: {imagePath}")
        continue

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Use face_recognition to locate faces
    boxes = face_recognition.face_locations(rgb, model='hog')

    # Compute the facial embeddings for the faces
    encodings = face_recognition.face_encodings(rgb, boxes)

    # Loop over the encodings
    for encoding in encodings:
        knownEncodings.append(encoding)
        knownNames.append(name)

# Save encodings along with their names in a dictionary
data = {"encodings": knownEncodings, "names": knownNames}

# Use pickle to save data into a file for later use
with open("face_enc", "wb") as f:
    f.write(pickle.dumps(data))

print("Face encodings saved to 'face_enc'")
