import torch
from joblib import dump
import clip
import os


def make_clip_model():
    controller_folder = 'controller'

    file_path = os.path.join(controller_folder, 'image-text-searcher-v-3.joblib')
    preprocessor_path = os.path.join(controller_folder, 'preprocessor-v-3.joblib')
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
        print('Downloading the models')
        model, preprocessor = clip.load('ViT-L/14', device)
        dump(value=model, filename=file_path)
        dump(value=preprocessor, filename=preprocessor_path)
        return 'Model and preprocessor Saved'

print(clip.available_models())