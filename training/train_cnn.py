"""
COMPLETE CNN TRAINING SCRIPT - BetaFarm AI
Purpose: Train MediumCNN (from scratch) + Pretrained Models (EfficientNet, MobileNet)

AUTHOR: BetaFarm AI Team
DATE: 2025
"""

# ============================================================
# SECTION 1: IMPORT LIBRARIES
# ============================================================
# Purpose: Import all necessary libraries for deep learning

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from pathlib import Path
import cv2
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import torchvision.models as models

print("=" * 60)
print("SECTION 1: IMPORTING LIBRARIES")
print("=" * 60)
print(f"✅ PyTorch version: {torch.__version__}")
print("✅ All libraries imported successfully")


# ============================================================
# SECTION 2: CUSTOM DATASET CLASS
# ============================================================
# Purpose: Load images from folders and assign labels

print("\n" + "=" * 60)
print("SECTION 2: CUSTOM DATASET CLASS")
print("=" * 60)

class PlantDataset(Dataset):
    """
    Custom Dataset for loading plant disease images.
    
    in_channels = 3 (RGB images: Red, Green, Blue)
    out_channels = 38 (disease classes)
    
    How it works:
    1. Reads all class folders (Apple___Apple_scab, etc.)
    2. Assigns ID 0-37 to each disease
    3. Stores image paths and labels
    4. Returns image + label when indexed
    """
    
    def __init__(self, root_dir, transform=None):
        """
        Initialize the dataset.
        
        Args:
            root_dir: Path to folder containing class subfolders (e.g., processed/train)
            transform: Optional transforms to apply to images (resize, flip, etc.)
        """
        # Convert to Path object for easier path handling
        self.root_dir = Path(root_dir)
        self.transform = transform
        
        # Get all class folders (each folder = one disease)
        # [f for f in ... if f.is_dir()] = only folders, not files
        self.classes = [f.name for f in self.root_dir.iterdir() if f.is_dir()]
        self.classes.sort()  # Sort alphabetically for consistent ordering
        
        # Create mapping: class name → class ID
        # Example: {'Apple___Apple_scab': 0, 'Apple___Black_rot': 1, ...}
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(self.classes)}
        
        # Store all image paths and their labels
        self.images = []  # List of image file paths
        self.labels = []  # List of corresponding class IDs
        
        # Loop through each class folder
        for class_name in self.classes:
            class_folder = self.root_dir / class_name
            class_idx = self.class_to_idx[class_name]
            
            # Find all images in this class folder
            # *.JPG for uppercase extension, *.jpg for lowercase
            for img_path in list(class_folder.glob("*.JPG")) + list(class_folder.glob("*.jpg")):
                self.images.append(img_path)
                self.labels.append(class_idx)
        
        print(f"✅ Dataset initialized")
        print(f"   Root: {root_dir}")
        print(f"   Classes: {len(self.classes)}")
        print(f"   Total images: {len(self.images)}")
        print(f"   in_channels: 3 (RGB)")
        print(f"   out_channels: {len(self.classes)} (diseases)")
    
    def __len__(self):
        """Return total number of images in the dataset."""
        return len(self.images)
    
    def __getitem__(self, idx):
        """
        Load and return image and label at index.
        
        Args:
            idx: Index of the image to load
            
        Returns:
            image: Tensor of shape (3, 224, 224)
            label: Integer class ID (0 to 37)
        """
        # Get image path and label
        img_path = self.images[idx]
        label = self.labels[idx]
        
        # Read image using OpenCV
        # cv2.imread() reads image in BGR format
        image = cv2.imread(str(img_path))
        
        # Convert BGR to RGB (PyTorch models expect RGB)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Apply transforms (resize, normalize, etc.) if any
        if self.transform:
            image = self.transform(image)
        
        return image, label


# ============================================================
# DEFINE TRANSFORMS (Data Augmentation)
# ============================================================
# Purpose: Preprocess images before feeding to model

# Training transforms - includes random augmentation
# Reason: Helps model generalize better (prevent overfitting)
train_transform = transforms.Compose([
    transforms.ToPILImage(),                    # Convert numpy array to PIL Image
    transforms.Resize((224, 224)),              # Resize all images to 224x224
    transforms.RandomHorizontalFlip(p=0.5),     # Flip image horizontally with 50% chance
    transforms.RandomRotation(degrees=15),      # Rotate image ±15 degrees
    transforms.ToTensor(),                      # Convert to PyTorch tensor (0-1 range)
    transforms.Normalize(                       # Normalize to [-1, 1] range
        mean=[0.485, 0.456, 0.406],             # ImageNet mean (RGB)
        std=[0.229, 0.224, 0.225]               # ImageNet std (RGB)
    )
])

# Validation transforms - no random augmentation
# Reason: Validation must be consistent to get reliable metrics
val_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

print("✅ Transforms defined")
print("   Training: Resize + RandomFlip + RandomRotation + Normalize")
print("   Validation: Resize + Normalize only")


# ============================================================
# SECTION 3: MEDIUMCNN MODEL (FROM SCRATCH)
# ============================================================
# Purpose: Build CNN from scratch using Sequential layers

print("\n" + "=" * 60)
print("SECTION 3: MEDIUMCNN MODEL (FROM SCRATCH)")
print("=" * 60)

class CropCNN(nn.Module):
    """
    Medium CNN with 4 convolutional layers built using Sequential.
    
    in_channels = 3 (RGB image: Red, Green, Blue)
    out_channels = 38 (number of disease classes)
    
    Channel flow visualization:
    Input:  (3, 224, 224)  - RGB image
    Conv1:  (64, 222, 222) - 64 filters (edge detection)
    Pool1:  (64, 111, 111) - MaxPool halves size
    Conv2:  (128, 109, 109) - 128 filters (shape detection)
    Pool2:  (128, 54, 54)   - MaxPool halves size
    Conv3:  (256, 52, 52)   - 256 filters (pattern detection)
    Pool3:  (256, 26, 26)   - MaxPool halves size
    Conv4:  (512, 24, 24)   - 512 filters (disease features)
    Pool4:  (512, 12, 12)   - MaxPool halves size
    Flatten: (512*12*12=73728) - Convert 2D to 1D
    FC1:    (512)           - First dense layer
    Dropout: (512)          - Prevent overfitting
    FC2:    (38)            - Output (38 diseases)
    """
    
    def __init__(self, in_channels=3, out_channels=38):
        """
        Initialize the MediumCNN architecture.
        
        Args:
            in_channels (int): Number of input channels (3 for RGB)
            out_channels (int): Number of output classes (38 diseases)
        """
        super(CropCNN, self).__init__()
        
        # Store channels for reference (useful for debugging)
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        # ============================================================
        # FEATURE EXTRACTION LAYERS (Convolutional Base)
        # Sequential = layers applied in order: 1 → 2 → 3 → 4
        # ============================================================
        
        self.features = nn.Sequential(
            # ---------- BLOCK 1: 3 → 64 channels ----------
            # Conv2d: 2D convolution, learns features from image
            # in_channels=3 (RGB), out_channels=64 (filters)
            # kernel_size=3: 3x3 filter, padding=1: keeps same size
            nn.Conv2d(in_channels, 64, kernel_size=3, padding=1),
            # BatchNorm: Normalizes outputs for faster training
            nn.BatchNorm2d(64),
            # ReLU: Activation function (turns negatives to 0)
            nn.ReLU(inplace=True),
            # MaxPool2d: Reduces size by half (224 → 112)
            nn.MaxPool2d(kernel_size=2, stride=2),
            
            # ---------- BLOCK 2: 64 → 128 channels ----------
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # 112 → 56
            
            # ---------- BLOCK 3: 128 → 256 channels ----------
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # 56 → 28
            
            # ---------- BLOCK 4: 256 → 512 channels ----------
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # 28 → 14
        )
        
        # Calculate flattened size after convolutions
        # Input: 224x224
        # After 4 MaxPool layers: 224 / 2 / 2 / 2 / 2 = 14
        # Then multiply by channels (512) → 512 * 14 * 14 = 100,352
        self.flatten_size = 512 * 14 * 14
        print(f"   CropCNN flatten size: {self.flatten_size}")
        
        # ============================================================
        # CLASSIFICATION LAYERS (Fully Connected)
        # ============================================================
        
        self.classifier = nn.Sequential(
            # Flatten: Converts (512, 14, 14) → (100,352)
            nn.Flatten(),
            # First FC layer: 100,352 → 512
            nn.Linear(self.flatten_size, 512),
            nn.ReLU(inplace=True),
            # Dropout: Randomly turns off 40% of neurons
            # Helps prevent overfitting
            nn.Dropout(0.4),
            # Output layer: 512 → out_channels (38 diseases)
            nn.Linear(512, out_channels)
        )
    
    def forward(self, x):
        """
        Forward pass: image → features → classification
        
        Args:
            x: Input tensor of shape (batch, in_channels, 224, 224)
            
        Returns:
            Output tensor of shape (batch, out_channels)
        """
        # Pass through convolutional layers (feature extraction)
        x = self.features(x)
        
        # Pass through fully connected layers (classification)
        x = self.classifier(x)
        
        return x


# Create MediumCNN instance
print("\n📋 Creating MediumCNN model...")
model_scratch = CropCNN(in_channels=3, out_channels=38)
print(f"\n✅ CropCNN (From Scratch)")
print(f"   in_channels: {model_scratch.in_channels}")
print(f"   out_channels: {model_scratch.out_channels}")
# Sum of all parameters (weights + biases)
total_params = sum(p.numel() for p in model_scratch.parameters())
print(f"   Total parameters: {total_params:,}")


# ============================================================
# SECTION 4: PRETRAINED MODELS
# ============================================================
# Purpose: Use models pre-trained on ImageNet (transfer learning)

print("\n" + "=" * 60)
print("SECTION 4: PRETRAINED MODELS")
print("=" * 60)


class EfficientNetModel(nn.Module):
    """
    EfficientNetB0 pretrained on ImageNet (transfer learning).
    
    in_channels = 3 (RGB images)
    out_channels = 38 (plant diseases)
    
    Why EfficientNet?
    - Better accuracy than ResNet with fewer parameters
    - State-of-the-art for image classification
    - Scaled efficiently (width, depth, resolution)
    """
    
    def __init__(self, in_channels=3, out_channels=38):
        super(EfficientNetModel, self).__init__()
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        # Load pretrained EfficientNetB0
        # 'DEFAULT' loads the best available weights
        # If hash error occurs, change to 'pretrained=True'
        print("   Loading pretrained EfficientNetB0...")
        try:
            self.model = models.efficientnet_b0(weights='DEFAULT')
        except:
            print("   Falling back to pretrained=True...")
            self.model = models.efficientnet_b0(pretrained=True)
        
        # FREEZE all layers (don't train them)
        # This preserves the pretrained knowledge from ImageNet
        for param in self.model.parameters():
            param.requires_grad = False
        
        # Get the number of input features to the final layer
        # EfficientNetB0's classifier: (1280, 1000)
        # 1280 features → 1000 ImageNet classes
        in_features = self.model.classifier[1].in_features
        print(f"   Original classifier: {in_features} → 1000 (ImageNet)")
        
        # Replace the final classifier layer
        # New layer: in_features (1280) → out_channels (38)
        self.model.classifier = nn.Sequential(
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(in_features, out_channels)
        )
        print(f"   New classifier: {in_features} → {out_channels} (plant diseases)")
    
    def forward(self, x):
        """Forward pass through EfficientNet."""
        return self.model(x)


class MobileNetModel(nn.Module):
    """
    MobileNetV3 pretrained on ImageNet (transfer learning).
    
    in_channels = 3
    out_channels = 38
    
    Why MobileNet?
    - Very lightweight (2.5M parameters vs 25M for ResNet50)
    - Designed specifically for mobile phones
    - Optimized for speed and efficiency
    - Perfect for deployment on farmer's phones
    """
    
    def __init__(self, in_channels=3, out_channels=38):
        super(MobileNetModel, self).__init__()
        
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        # Load pretrained MobileNetV3 Large
        print("   Loading pretrained MobileNetV3...")
        self.model = models.mobilenet_v3_large(weights='DEFAULT')
        
        # Freeze all layers (preserve pretrained knowledge)
        for param in self.model.parameters():
            param.requires_grad = False
        
        # Replace classifier head
        # MobileNetV3 classifier structure: Linear → Hardswish → Linear
        # We access classifier[3] to get the last Linear layer
        in_features = self.model.classifier[3].in_features
        print(f"   Original classifier: {in_features} → 1000 (ImageNet)")
        
        # Create new classifier for 38 plant diseases
        self.model.classifier = nn.Sequential(
            nn.Linear(in_features, 512),      # 1280 → 512
            nn.Hardswish(),                   # Activation function
            nn.Dropout(p=0.2, inplace=True),  # Prevent overfitting
            nn.Linear(512, out_channels)      # 512 → 38
        )
        print(f"   New classifier: {in_features} → 512 → {out_channels}")
    
    def forward(self, x):
        """Forward pass through MobileNet."""
        return self.model(x)


# Create pretrained model instances
print("\n📋 Creating pretrained models...")

# EfficientNet (may have download issues - if so, comment out)
try:
    model_efficientnet = EfficientNetModel(in_channels=3, out_channels=38)
    print(f"\n✅ EfficientNetB0 (Pretrained)")
    print(f"   in_channels: {model_efficientnet.in_channels}")
    print(f"   out_channels: {model_efficientnet.out_channels}")
    trainable = sum(p.numel() for p in model_efficientnet.parameters() if p.requires_grad)
    print(f"   Trainable parameters: {trainable:,}")
except Exception as e:
    print(f"\n⚠️ EfficientNet failed to load: {e}")
    print("   Skipping EfficientNet...")
    model_efficientnet = None

# MobileNet (usually works)
model_mobilenet = MobileNetModel(in_channels=3, out_channels=38)
print(f"\n✅ MobileNetV3 (Pretrained)")
print(f"   in_channels: {model_mobilenet.in_channels}")
print(f"   out_channels: {model_mobilenet.out_channels}")
trainable = sum(p.numel() for p in model_mobilenet.parameters() if p.requires_grad)
print(f"   Trainable parameters: {trainable:,}")


# ============================================================
# SECTION 5: DEVICE SETUP
# ============================================================
# Purpose: Check if GPU is available, otherwise use CPU

print("\n" + "=" * 60)
print("SECTION 5: DEVICE SETUP")
print("=" * 60)

# torch.cuda.is_available() returns True if NVIDIA GPU is detected
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}")
if device == 'cpu':
    print("   ⚠️ Training on CPU will take longer (6-8 hours for 10 epochs)")
    print("   Consider using Google Colab for free GPU training")
else:
    print("   ✅ GPU detected! Training will be faster (20-30 minutes)")

# Move models to device (CPU or GPU)
model_scratch = model_scratch.to(device)
model_mobilenet = model_mobilenet.to(device)
if model_efficientnet:
    model_efficientnet = model_efficientnet.to(device)


# ============================================================
# SECTION 6: LOAD DATASET
# ============================================================
# Purpose: Load preprocessed images from disk

print("\n" + "=" * 60)
print("SECTION 6: LOADING DATASET")
print("=" * 60)

# Path to preprocessed images (resized to 224x224)
processed_path = Path(__file__).parent.parent / 'datasets' / 'new_plant_diseases' / 'processed'
train_path = processed_path / 'train'    # Training images
val_path = processed_path / 'val'        # Validation images

print(f"Train path: {train_path}")
print(f"Val path: {val_path}")

# Create datasets (loads all image paths)
print("\n📂 Loading training dataset...")
train_dataset = PlantDataset(train_path, transform=train_transform)

print("\n📂 Loading validation dataset...")
val_dataset = PlantDataset(val_path, transform=val_transform)

# Create DataLoaders (batch processing)
# batch_size=32: Process 32 images at once
# shuffle=True: Randomize order (training only)
# num_workers=4: Use 4 CPU cores for loading
batch_size = 32
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

print(f"\n✅ Data loaders created")
print(f"   Batch size: {batch_size}")
print(f"   Training batches: {len(train_loader)}")
print(f"   Validation batches: {len(val_loader)}")


# ============================================================
# SECTION 7: TRAINING FUNCTION
# ============================================================
# Purpose: Train a model for multiple epochs

print("\n" + "=" * 60)
print("SECTION 7: TRAINING FUNCTION")
print("=" * 60)

def train_model(model, model_name, train_loader, val_loader, epochs=10, lr=0.001):
    """
    Train a model and return training history.
    
    Args:
        model: PyTorch model to train
        model_name: Name of the model (for printing and saving)
        train_loader: DataLoader for training data
        val_loader: DataLoader for validation data
        epochs: Number of epochs (passes through entire dataset)
        lr: Learning rate (how fast model learns)
    
    Returns:
        history: Dictionary with loss and accuracy per epoch
        best_accuracy: Best validation accuracy achieved
    """
    
    # CrossEntropyLoss: For multi-class classification (38 diseases)
    criterion = nn.CrossEntropyLoss()
    
    # Adam optimizer: Adapts learning rate automatically
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    # Store training history for plotting
    history = {
        'train_loss': [],
        'val_loss': [],
        'train_acc': [],
        'val_acc': []
    }
    
    best_acc = 0.0
    
    # Loop through each epoch
    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs}")
        print("-" * 40)
        
        # ========== TRAINING PHASE ==========
        model.train()  # Set model to training mode (enables dropout, etc.)
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        # tqdm shows progress bar
        for images, labels in tqdm(train_loader, desc="  Training"):
            # Move data to device (CPU/GPU)
            images, labels = images.to(device), labels.to(device)
            
            # Forward pass: images → predictions
            outputs = model(images)
            
            # Calculate loss (how wrong the model is)
            loss = criterion(outputs, labels)
            
            # Backward pass: calculate gradients
            optimizer.zero_grad()  # Reset gradients
            loss.backward()        # Compute gradients
            optimizer.step()       # Update weights
            
            # Statistics
            train_loss += loss.item()
            _, predicted = torch.max(outputs, 1)  # Get predicted class
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
        
        train_acc = 100 * train_correct / train_total
        avg_train_loss = train_loss / len(train_loader)
        
        # ========== VALIDATION PHASE ==========
        model.eval()  # Set model to evaluation mode
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        # torch.no_grad(): Disable gradient calculation (saves memory)
        with torch.no_grad():
            for images, labels in tqdm(val_loader, desc="  Validation"):
                images, labels = images.to(device), labels.to(device)
                
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        val_acc = 100 * val_correct / val_total
        avg_val_loss = val_loss / len(val_loader)
        
        # Store history
        history['train_loss'].append(avg_train_loss)
        history['val_loss'].append(avg_val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)
        
        # Print results
        print(f"\n  📊 Results:")
        print(f"     Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"     Val Loss: {avg_val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            save_dir = Path(__file__).parent / 'saved_models'
            save_dir.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), save_dir / f'{model_name}_best.pth')
            print(f"     💾 Best model saved! (Acc: {best_acc:.2f}%)")
    
    return history, best_acc


def plot_training_history(history, model_name):
    """
    Plot training and validation loss/accuracy curves.
    
    Args:
        history: Dictionary from train_model()
        model_name: Name of the model (for file naming)
    """
    
    # Create figure with 2 subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Left plot: Loss curves
    ax1.plot(history['train_loss'], 'b-', label='Train Loss')
    ax1.plot(history['val_loss'], 'r-', label='Val Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title(f'{model_name} - Loss Curves')
    ax1.legend()
    ax1.grid(True)
    
    # Right plot: Accuracy curves
    ax2.plot(history['train_acc'], 'b-', label='Train Accuracy')
    ax2.plot(history['val_acc'], 'r-', label='Val Accuracy')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title(f'{model_name} - Accuracy Curves')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    
    # Save plot to file
    save_dir = Path(__file__).parent / 'results' / 'plots'
    save_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_dir / f'{model_name}_training_curves.png', dpi=150)
    plt.show()
    
    print(f"   📊 Plot saved to: {save_dir / f'{model_name}_training_curves.png'}")


# ============================================================
# SECTION 8: TRAIN ALL MODELS
# ============================================================
# Purpose: Train each model and record results

print("\n" + "=" * 60)
print("SECTION 8: TRAINING ALL MODELS")
print("=" * 60)

results = {}

# ========== Model 1: MediumCNN (From Scratch) ==========
print("\n" + "=" * 50)
print("TRAINING CropCNN (FROM SCRATCH)")
print("=" * 50)
print("   Learning rate: 0.001")
print("   Epochs: 10")

history1, acc1 = train_model(
    model_scratch, 
    "CropCNN", 
    train_loader, 
    val_loader, 
    epochs=10, 
    lr=0.001
)
plot_training_history(history1, "CropCNN")
results['CropCNN'] = acc1

# ========== Model 2: MobileNet (Pretrained) ==========
print("\n" + "=" * 50)
print("TRAINING MOBILENET (PRETRAINED)")
print("=" * 50)
print("   Learning rate: 0.0001 (lower for fine-tuning)")
print("   Epochs: 10")

history2, acc2 = train_model(
    model_mobilenet, 
    "MobileNet", 
    train_loader, 
    val_loader, 
    epochs=10, 
    lr=0.0001
)
plot_training_history(history2, "MobileNet")
results['MobileNet'] = acc2

# ========== Model 3: EfficientNet (if loaded successfully) ==========
if model_efficientnet:
    print("\n" + "=" * 50)
    print("TRAINING EFFICIENTNET (PRETRAINED)")
    print("=" * 50)
    print("   Learning rate: 0.0001 (lower for fine-tuning)")
    print("   Epochs: 10")
    
    history3, acc3 = train_model(
        model_efficientnet, 
        "EfficientNet", 
        train_loader, 
        val_loader, 
        epochs=10, 
        lr=0.0001
    )
    plot_training_history(history3, "EfficientNet")
    results['EfficientNet'] = acc3


# ============================================================
# SECTION 9: RESULTS SUMMARY
# ============================================================
# Purpose: Display and save final results

print("\n" + "=" * 60)
print("SECTION 9: RESULTS SUMMARY")
print("=" * 60)

print("\n📊 FINAL VALIDATION ACCURACY:")
print("-" * 40)
for model_name, acc in results.items():
    print(f"   {model_name}: {acc:.2f}%")

# Find best model (highest accuracy)
best_model = max(results, key=results.get)
print(f"\n🏆 BEST MODEL: {best_model} with {results[best_model]:.2f}% accuracy")

print("\n📈 MODEL COMPARISON:")
print("-" * 40)
print(f"   CropCNN (From Scratch): {results['CropCNN']:.2f}% - {sum(p.numel() for p in model_scratch.parameters()):,} params")
print(f"   MobileNet (Pretrained): {results['MobileNet']:.2f}% - {sum(p.numel() for p in model_mobilenet.parameters() if p.requires_grad):,} trainable params")
if 'EfficientNet' in results:
    print(f"   EfficientNet (Pretrained): {results['EfficientNet']:.2f}% - {sum(p.numel() for p in model_efficientnet.parameters() if p.requires_grad):,} trainable params")

# Save results to text file
results_path = Path(__file__).parent / 'results'
results_path.mkdir(parents=True, exist_ok=True)

with open(results_path / 'training_results.txt', 'w') as f:
    f.write("=" * 60 + "\n")
    f.write("BETAFARM AI - CNN TRAINING RESULTS\n")
    f.write("=" * 60 + "\n\n")
    
    f.write("FINAL VALIDATION ACCURACY:\n")
    f.write("-" * 40 + "\n")
    for model_name, acc in results.items():
        f.write(f"{model_name}: {acc:.2f}%\n")
    
    f.write(f"\nBest model: {best_model} ({results[best_model]:.2f}%)\n")
    
    f.write("\nMODEL DETAILS:\n")
    f.write("-" * 40 + "\n")
    f.write(f"CropCNN: {sum(p.numel() for p in model_scratch.parameters()):,} parameters\n")
    f.write(f"MobileNet: {sum(p.numel() for p in model_mobilenet.parameters() if p.requires_grad):,} trainable parameters\n")
    if 'EfficientNet' in results:
        f.write(f"EfficientNet: {sum(p.numel() for p in model_efficientnet.parameters() if p.requires_grad):,} trainable parameters\n")

print(f"\n✅ Results saved to: {results_path / 'training_results.txt'}")

print("\n" + "=" * 60)
print("🎉 TRAINING COMPLETE!")
print("=" * 60)
print("\n📁 Saved files:")
print(f"   - saved_models/CropCNN_best.pth")
print(f"   - saved_models/MobileNet_best.pth")
if 'EfficientNet' in results:
    print(f"   - saved_models/EfficientNet_best.pth")
print(f"   - results/plots/*_training_curves.png")
print(f"   - results/training_results.txt")