from sentence_transformers import SentenceTransformer
import torch
from joblib import dump
import os


def make_clip_model():
    controller_folder = 'controller'

    file_path = os.path.join(controller_folder, 'image-text-searcher-v-2.joblib')
    file_path = os.path.abspath(file_path)
    print(file_path)
    if os.path.exists(file_path):
        print('Exists')
        return 'Model already exists'
    else:
        device = 'cpu'
        if torch.cuda.is_available():
            device = 'cuda'
        elif torch.backends.mps.is_available():
            device = 'mps'
        print('Downloading the model')
        model = SentenceTransformer('clip-ViT-B-32', device=device)
        dump(value=model, filename=file_path)
        return 'Model Saved'
