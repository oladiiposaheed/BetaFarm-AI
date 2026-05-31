"""
Simple test for ImageProcessor - Process one image and show before/after
"""

import cv2
from pathlib import Path
import matplotlib.pyplot as plt

# Find a sample image
train_path = Path(__file__).parent.parent / 'datasets' / 'new_plant_diseases' / 'train'
class_folder = list(train_path.iterdir())[0]  # First class folder
image_path = list(class_folder.glob('*.JPG'))[0]  # First image

# Read and resize
img = cv2.imread(str(image_path))
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_resized = cv2.resize(img_rgb, (224, 224))

# Display before/after
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
ax1.imshow(img_rgb)
ax1.set_title(f'BEFORE\n{class_folder.name}\n{img.shape[1]}x{img.shape[0]}')
ax1.axis('off')

ax2.imshow(img_resized)
ax2.set_title(f'AFTER (224x224)\n{class_folder.name}')
ax2.axis('off')

plt.suptitle('Before vs After Resizing')
plt.tight_layout()
plt.show()

print(f"✅ Processed: {image_path.name}")
print(f"   Original: {img.shape[1]}x{img.shape[0]}")
print(f"   Resized: 224x224")