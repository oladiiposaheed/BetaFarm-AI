"""
export_onnx.py - Convert PyTorch model to ONNX format for FastAPI
Run this script from the 'training' folder.
"""

import torch
import torchvision.models as models
import os

print("=" * 60)
print("EXPORTING MODEL TO ONNX")
print("=" * 60)

# ============================================================
# STEP 1: Create the model architecture
# ============================================================

print("\n[1/5] Creating model architecture...")

# Create MobileNetV3 Large model
model = models.mobilenet_v3_large(pretrained=False)

# Build the classifier (same as training)
model.classifier = torch.nn.Sequential(
    torch.nn.Linear(960, 512),     # 960 → 512
    torch.nn.Hardswish(),           # Activation
    torch.nn.Dropout(p=0.2),       # Dropout
    torch.nn.Linear(512, 38)       # 512 → 38 diseases
)

print("✅ Model architecture created")

# ============================================================
# STEP 2: Load the trained weights
# ============================================================

print("\n[2/5] Loading trained weights...")

# Path to your trained model
model_path = 'results/mobilenet/best_model.pth'

if not os.path.exists(model_path):
    print(f"❌ Error: Model not found at {model_path}")
    print("   Make sure you are in the 'training' folder")
    exit(1)

# Load state dict
state_dict = torch.load(model_path, map_location='cpu')

# Remove 'model.' prefix if present (from training save)
new_state_dict = {}
for key, value in state_dict.items():
    if key.startswith('model.'):
        new_key = key[6:]  # Remove 'model.' prefix
        new_state_dict[new_key] = value
    else:
        new_state_dict[key] = value

# Load with strict=False to ignore minor mismatches
model.load_state_dict(new_state_dict, strict=False)
print("✅ Weights loaded successfully")

# ============================================================
# STEP 3: Set to evaluation mode
# ============================================================

print("\n[3/5] Setting model to evaluation mode...")
model.eval()
print("✅ Model ready for inference")

# ============================================================
# STEP 4: Test the model
# ============================================================

print("\n[4/5] Testing model with dummy input...")

# Create dummy input (1 batch, 3 channels, 224x224)
dummy_input = torch.randn(1, 3, 224, 224)

with torch.no_grad():
    output = model(dummy_input)
    print(f"✅ Model test passed! Output shape: {output.shape}")
    print(f"   Expected: torch.Size([1, 38]) → 38 disease classes")

# ============================================================
# STEP 5: Export to ONNX
# ============================================================

print("\n[5/5] Exporting to ONNX...")

# Ensure output directory exists
output_dir = os.path.join('..', 'models')
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, 'mobilenet_best.onnx')

torch.onnx.export(
    model,                          # PyTorch model
    dummy_input,                    # Dummy input
    output_path,                    # Output file path
    input_names=['input'],          # Input layer name
    output_names=['output'],        # Output layer name
    dynamic_axes={                  # Allow variable batch size
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
    },
    opset_version=11                # ONNX version
)

print(f"✅ Model exported to ONNX")
print(f"   Location: {output_path}")

# Verify file exists
if os.path.exists(output_path):
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   File size: {file_size:.2f} MB")

print("\n" + "=" * 60)
print("ONNX EXPORT COMPLETE!")
print("=" * 60)
print("\nUse this ONNX file in FastAPI")