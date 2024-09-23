import face_recognition
import cv2
from PIL import Image, ImageDraw
from facenet_pytorch import MTCNN, extract_face, InceptionResnetV1
import torch
import numpy as np

image_path = 'static/uploads/images/IMG-20240918-WA0269.jpg'

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
image = Image.open(image_path)
resnet = InceptionResnetV1(pretrained='vggface2').eval()
mtcnn = MTCNN(image_size=240)
faces, probs = mtcnn.detect(image)

for face, prob in zip(faces, probs):
    if prob < 0.98:
        continue

    face_img = Image.fromarray(face)
    face_emb = resnet(face_img.unsqueeze(0))

    face_img.save(f"face_{prob:.2f}.png")

# image_draw = image.copy()
# draw = ImageDraw.Draw(image_draw)
#
# for i, (box, point) in enumerate(zip(boxes, points)):
#     draw.rectangle(box.tolist(), width=5)
#     for p in point:
#         draw.rectangle((p - 10).tolist() + (p + 10).tolist(), width=10)
#     extract_face(image, box, save_path='detected_face_{}.png'.format(i))
#
# image_draw.save('annotated_faces.png')
