"""
train_mobilenet.py - Train MobileNet with Full Visualizations (4 Epochs)
Includes: Real-time progress, Loss curves, Accuracy curves, Confusion Matrix
"""

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
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns

# ============================================================
# DATASET CLASS
# ============================================================

class PlantDataset(Dataset):
    """Custom dataset for plant disease images"""
    
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        
        # Get all class folders
        self.classes = [f.name for f in self.root_dir.iterdir() if f.is_dir()]
        self.classes.sort()
        
        # Create class to index mapping
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(self.classes)}
        
        # Store all image paths and labels
        self.images = []
        self.labels = []
        
        for class_name in self.classes:
            class_folder = self.root_dir / class_name
            class_idx = self.class_to_idx[class_name]
            for img_path in list(class_folder.glob("*.JPG")) + list(class_folder.glob("*.jpg")):
                self.images.append(img_path)
                self.labels.append(class_idx)
        
        print(f"Dataset: {len(self.images)} images, {len(self.classes)} classes")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        label = self.labels[idx]
        
        # Read image
        image = cv2.imread(str(img_path))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


# ============================================================
# DATA TRANSFORMS
# ============================================================

train_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


# ============================================================
# MOBILENET MODEL
# ============================================================

class MobileNetModel(nn.Module):
    """MobileNetV3 with custom classifier for 38 diseases"""
    
    def __init__(self, out_channels=38):
        super(MobileNetModel, self).__init__()
        
        # Load pretrained MobileNetV3 Large
        self.model = models.mobilenet_v3_large(weights='DEFAULT')
        
        # Freeze all layers (preserve pretrained knowledge)
        for param in self.model.parameters():
            param.requires_grad = False
        
        # Get input features from the first Linear layer
        in_features = self.model.classifier[0].in_features  # This gives 960
        print(f"Detected input features: {in_features}")
        
        # Replace classifier for 38 diseases
        self.model.classifier = nn.Sequential(
            nn.Linear(in_features, 512),     # 960 → 512
            nn.Hardswish(),
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(512, out_channels)     # 512 → 38
        )
    
    def forward(self, x):
        return self.model(x)


# ============================================================
# VISUALIZATION FUNCTIONS
# ============================================================

def plot_training_history(history, save_dir):
    """Plot and save training loss and accuracy curves"""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss Curves
    epochs = range(1, len(history['train_loss']) + 1)
    ax1.plot(epochs, history['train_loss'], 'b-', label='Training Loss', linewidth=2)
    ax1.plot(epochs, history['val_loss'], 'r-', label='Validation Loss', linewidth=2)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Accuracy Curves
    ax2.plot(epochs, history['train_acc'], 'b-', label='Training Accuracy', linewidth=2)
    ax2.plot(epochs, history['val_acc'], 'r-', label='Validation Accuracy', linewidth=2)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title('Training and Validation Accuracy')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_dir / 'training_history.png', dpi=150, bbox_inches='tight')
    plt.show()
    print(f"Training history plot saved to {save_dir / 'training_history.png'}")


def plot_confusion_matrix(model, val_loader, classes, device, save_dir):
    """Plot and save confusion matrix"""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="  Computing confusion matrix"):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    cm = confusion_matrix(all_labels, all_preds)
    
    # Show top 15 classes for readability
    num_classes_to_show = min(15, len(classes))
    cm_subset = cm[:num_classes_to_show, :num_classes_to_show]
    class_subset = classes[:num_classes_to_show]
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm_subset, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_subset, yticklabels=class_subset)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title(f'Confusion Matrix (First {num_classes_to_show} Classes)')
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()
    plt.savefig(save_dir / 'confusion_matrix.png', dpi=150, bbox_inches='tight')
    plt.show()
    print(f"Confusion matrix saved to {save_dir / 'confusion_matrix.png'}")


def save_classification_report(model, val_loader, classes, device, save_dir):
    """Generate and save classification report"""
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="  Generating classification report"):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    report = classification_report(all_labels, all_preds, target_names=classes, output_dict=True)
    
    with open(save_dir / 'classification_report.txt', 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CLASSIFICATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(classification_report(all_labels, all_preds, target_names=classes))
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Overall Accuracy: {report['accuracy']*100:.2f}%\n")
        f.write(f"Macro Avg Precision: {report['macro avg']['precision']*100:.2f}%\n")
        f.write(f"Macro Avg Recall: {report['macro avg']['recall']*100:.2f}%\n")
        f.write(f"Macro Avg F1-Score: {report['macro avg']['f1-score']*100:.2f}%\n")
    
    print(f"Classification report saved to {save_dir / 'classification_report.txt'}")
    print(f"\nOverall Accuracy: {report['accuracy']*100:.2f}%")
    print(f"Macro Avg F1-Score: {report['macro avg']['f1-score']*100:.2f}%")


# ============================================================
# TRAINING FUNCTION WITH REAL-TIME PROGRESS
# ============================================================

def train_model(model, train_loader, val_loader, epochs, lr, device, save_dir):
    """
    Train model and return training history with real-time progress updates
    """
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    history = {
        'train_loss': [],
        'val_loss': [],
        'train_acc': [],
        'val_acc': []
    }
    
    best_val_acc = 0.0
    
    print("\n" + "=" * 70)
    print("STARTING TRAINING - 4 EPOCHS")
    print("=" * 70)
    print(f"Total training batches: {len(train_loader)}")
    print(f"Total validation batches: {len(val_loader)}")
    print(f"Each batch = 32 images")
    print("=" * 70)
    
    for epoch in range(epochs):
        print(f"\n{'='*50}")
        print(f"EPOCH {epoch+1}/{epochs}")
        print(f"{'='*50}")
        
        # ========== TRAINING PHASE ==========
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        print(f"\n[Training] Processing {len(train_loader)} batches...")
        
        for batch_idx, (images, labels) in enumerate(tqdm(train_loader, desc="  Training Progress")):
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
            
            # Show progress every 500 batches
            if (batch_idx + 1) % 500 == 0:
                current_acc = 100 * train_correct / train_total
                print(f"     Batch {batch_idx+1}/{len(train_loader)}: Loss: {loss.item():.4f}, Running Acc: {current_acc:.2f}%")
        
        train_acc = 100 * train_correct / train_total
        avg_train_loss = train_loss / len(train_loader)
        
        # ========== VALIDATION PHASE ==========
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        print(f"\n[Validation] Processing {len(val_loader)} batches...")
        
        with torch.no_grad():
            for batch_idx, (images, labels) in enumerate(tqdm(val_loader, desc="  Validation Progress")):
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
        
        # Print epoch results
        print(f"\n{'='*50}")
        print(f"EPOCH {epoch+1} RESULTS")
        print(f"{'='*50}")
        print(f"Training Loss: {avg_train_loss:.4f}")
        print(f"Training Accuracy: {train_acc:.2f}%")
        print(f"Validation Loss: {avg_val_loss:.4f}")
        print(f"Validation Accuracy: {val_acc:.2f}%")
        print(f"{'='*50}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), save_dir / 'best_model.pth')
            print(f" Best model saved! (Val Acc: {best_val_acc:.2f}%)")
    
    return history, best_val_acc


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("MOBILENET TRAINING (4 EPOCHS)")
    print("=" * 60)
    
    # ========== DEVICE SETUP ==========
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n💻 Device: {device}")
    
    # ========== PATHS ==========
    processed_path = Path(__file__).parent.parent / 'datasets' / 'new_plant_diseases' / 'processed'
    train_path = processed_path / 'train'
    val_path = processed_path / 'val'
    
    results_dir = Path(__file__).parent / 'results' / 'mobilenet'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nTrain path: {train_path}")
    print(f"Val path: {val_path}")
    print(f"Results dir: {results_dir}")
    
    # ========== LOAD DATA ==========
    print("\nLoading datasets...")
    train_dataset = PlantDataset(train_path, transform=train_transform)
    val_dataset = PlantDataset(val_path, transform=val_transform)
    
    batch_size = 32
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    print(f"Training batches: {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    
    class_names = train_dataset.classes
    
    # ========== CREATE MODEL ==========
    print("\nCreating MobileNet model...")
    model = MobileNetModel(out_channels=38).to(device)
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable parameters: {trainable_params:,}")
    
    # ========== TRAIN MODEL (4 EPOCHS) ==========
    EPOCHS = 4  # ← CHANGED FROM 10 TO 4
    
    history, best_acc = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=EPOCHS,
        lr=0.0001,
        device=device,
        save_dir=results_dir
    )
    
    # ========== LOAD BEST MODEL FOR EVALUATION ==========
    model.load_state_dict(torch.load(results_dir / 'best_model.pth'))
    
    # ========== VISUALIZATIONS ==========
    print("\n" + "=" * 60)
    print("GENERATING VISUALIZATIONS")
    print("=" * 60)
    
    print("\nPlotting training history...")
    plot_training_history(history, results_dir)
    
    print("\nGenerating confusion matrix...")
    plot_confusion_matrix(model, val_loader, class_names, device, results_dir)
    
    print("\nGenerating classification report...")
    save_classification_report(model, val_loader, class_names, device, results_dir)
    
    # ========== FINAL SUMMARY ==========
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nBest Validation Accuracy: {best_acc:.2f}%")
    print(f"Number of Epochs: {EPOCHS}")
    print(f"\nResults saved to: {results_dir}")
    print(f"   - best_model.pth (model weights)")
    print(f"   - training_history.png (loss/accuracy curves)")
    print(f"   - confusion_matrix.png")
    print(f"   - classification_report.txt")