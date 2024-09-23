import torch
from PIL import Image
import numpy as np
import cv2
from facenet_pytorch import MTCNN

mtcnn = MTCNN()

image_path = 'static/uploads/images/IMG-20240918-WA0273.jpg'
image = Image.open(image_path)

boxes, probes = mtcnn.detect(image)

print(f"Detected {len(boxes)} faces")

for i, (box, prob) in enumerate(zip(boxes, probes)):
    if prob < 0.9:
        continue

    x1, y1, x2, y2 = [int(x) for x in box]

    face = np.array(image)[y1:y2, x1:x2]

    cv2.imwrite(f"face_{i+1}.jpg", face)