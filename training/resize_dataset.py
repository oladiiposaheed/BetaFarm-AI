"""
resize_dataset.py - Resize all images to 224x224
For New Plant Diseases Dataset (images are 256x256 → resize to 224x224)
"""

import cv2
from pathlib import Path
from tqdm import tqdm

# Paths
DATASET_ROOT = Path(__file__).parent.parent / 'datasets' / 'new_plant_diseases'
TARGET_SIZE = (224, 224)

print("=" * 60)
print("RESIZING DATASET")
print("=" * 60)
print(f"Source: {DATASET_ROOT}")
print(f"Target size: {TARGET_SIZE[0]}x{TARGET_SIZE[1]}")
print()

# Process train, valid, test folders
for split in ['train', 'valid', 'test']:
    source_dir = DATASET_ROOT / split
    dest_dir = DATASET_ROOT / 'processed' / split
    
    if not source_dir.exists():
        print(f"⚠️ {split} folder not found, skipping...")
        continue
    
    print(f"\n📁 Processing {split}...")
    
    # Get all class folders
    class_folders = [f for f in source_dir.iterdir() if f.is_dir()]
    
    for class_folder in tqdm(class_folders, desc=f"  {split} classes"):
        # Create destination folder
        dest_class = dest_dir / class_folder.name
        dest_class.mkdir(parents=True, exist_ok=True)
        
        # Get all images
        images = list(class_folder.glob('*.JPG')) + list(class_folder.glob('*.jpg'))
        
        for img_path in images:
            # Read image
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"    Warning: Could not read {img_path.name}")
                continue
            
            # Resize to 224x224
            img_resized = cv2.resize(img, TARGET_SIZE)
            
            # Save to processed folder
            output_path = dest_class / img_path.name
            cv2.imwrite(str(output_path), img_resized)
    
    print(f"  ✅ {split} complete")

print("\n" + "=" * 60)
print("✅ ALL IMAGES RESIZED!")
print("=" * 60)
print(f"\nOutput location: {DATASET_ROOT / 'processed'}")
print("   train/  - 70,295 images")
print("   val/  - 17,572 images")
print("   test/   - 13,200 images")