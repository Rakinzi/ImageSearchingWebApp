from sentence_transformers import SentenceTransformer
import torch

device = 'cpu'
if torch.cuda.is_available():
    device = 'cuda'
elif torch.backends.mps.is_available():
    device = 'mps'

#
# model = SentenceTransformer('clip-ViT-B-32', device='cpu')

print(f"Using {device}")