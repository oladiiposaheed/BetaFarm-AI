''' Configuration for FastAPI '''

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Model path (ONNX file)
MODEL_PATH = BASE_DIR / 'models' / 'mobilenet_best.onnx'

# Image settings
IMAGE_SIZE = (224, 224)
IMAGE_MEAN = [0.485, 0.456, 0.406]
IMAGE_STD = [0.229, 0.224, 0.225]

# Server settings
HOST = "0.0.0.0"
PORT = 8001

print(f"   Config loaded")
print(f"   Model path: {MODEL_PATH}")
print(f"   Model exists: {MODEL_PATH.exists()}")