import os
import cv2
import yaml
import numpy as np
from tqdm import tqdm
from pathlib import Path
import matplotlib.pyplot as plt
import albumentations as A
from PIL import Image


# Create AugmentationPipeline class
class AugmentationPipeline:
    '''
    Create augmentation pipeline for CNN  training and validation data
    Training: Applies random transformations to prevent overfitting and improve generalization.
    Validation: Only resize (no random transformations) to evaluate model performance on unseen data.
    '''
    
    def __init__(self, target_size=224):
        
        '''
        Initialize the augmentation pipeline with the target size for resizing images.
        
        Args:
            target_size (int): Target image size for resizing (width and height). Default is 224.
        '''
        self.target_size = target_size # Set the target size for resizing images
        print(f"Augmentation pipeline initialized with target size: {self.target_size}x{self.target_size}")
        
    def get_train_pipeline(self):
            '''
            Create augmentation pipeline for training data.
            Helps prevent overfitting(model performing well on unseen data) by introducing variability in the training data.
            Returns: A composed augmentation pipeline for training data.
            '''
            
            return A.Compose([
                A.Resize(self.target_size, self.target_size), # Resize images to target size
                A.HorizontalFlip(p=0.5), # Randomly flip images horizontally with a probability of 0.5
                A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.3), # Randomly adjust brightness and contrast with a probability of 0.3
                A.Rotate(limit=30, p=0.2), # Randomly rotate images within a limit of 30 degrees with a probability of 0.2
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)), # Normalize images using mean and std for pre-trained models
                A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=10, p=0.3), # Randomly adjust hue, saturation, and value with a probability of 0.3
                A.Normalize(mean=(0.45, 0.45, 0.406), std=(0.229, 0.224, 0.225)),
            ])
    
    
    # Create augmentation pipeline for validation data
    def get_val_pipeline(self):
        '''
        Create augmentation pipeline for validation/ data.
        Only resize images to the target size without applying random transformations.
        This ensures that the validation data remains consistent and allows for accurate evaluation of model performance on unseen data.
        Returns: A composed augmentation pipeline for validation data.
        '''
        return A.Compose([
               A.Resize(self.target_size, self.target_size), # Resize images to target size
               A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)), # Normalize images using mean and std for pre-trained models
            ])    
        
    
        
    def visualize_augmentations(self, image_path, num_examples=6, num_rows=2):
        '''
        Shows multiple augmented versions of the same image in a grid.
        ARGS:
            image_path: Path to a sample image
            num_examples: How many augmented versions to show
            num_rows: Number of rows in the grid (default 2)
        Uses get_train_pipeline() to create variations
        '''
        
        # Read the image
        img = cv2.imread(str(image_path))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Get original image size
        original_height, original_width = img.shape[:2]
        original_size_kb = os.path.getsize(str(image_path)) / 1024
        
        # Extract plant name from folder path
        plant_name = image_path.parent.name.replace('___', '-').replace('_', ' ')
        
        # Get the training pipeline
        train_pipeline = self.get_train_pipeline()
        
        # Create a figure with subplots
        fig, axes = plt.subplots(1, num_examples+1, figsize=(15, 4))
        
        # Show original
        axes[0].imshow(img)
        axes[0].set_title('ORIGINAL', fontsize=12)
        axes[0].axis('off')
        
        # Show augmented versions
        for i in range(num_examples):
            augemented = train_pipeline(image=img)
            aug_img = augemented['image']
            axes[i+1].imshow(aug_img)
            axes[i+1].set_title(f'Augmented {i+1}', fontsize=12)
            axes[i+1].axis('off')
            
        plt.suptitle('AugmentationPipeline - Same Image, Different Variations', fontsize=14)
        plt.tight_layout()
        
        # Save the visualization
        output_dir = Path(__file__).parent / 'results' / 'plots'
        output_dir.mkdir(parents=True, exist_ok=True)
        save_path = output_dir / 'augmentation_examples.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'\nVisualization saved to: {save_path}')
        plt.show()
        
        
#Test AugmentationPipeline
if __name__=='__main__':
    print('=' * 70)
    print('TESTING AUGMENTATIONPIPELINE CLASS')
    print('=' * 70)        
        
    #Create the pipeline
    print('\n[1] Creating AugmentationPipeline....')
    pipeline = AugmentationPipeline(target_size=224)
    
    #Find a sample image
    sample_image_path = Path(__file__).parent.parent / 'datasets' / 'new_plant_diseases' / 'train' / 'Apple___Apple_scab'
    
    # Get the first .JPG file
    if sample_image_path.exists():
        jpg_files = list(sample_image_path.glob('*.JPG*'))
        
        if jpg_files:
            sample_image = jpg_files[0]
            print(f'\n[2] Using sample image: {sample_image.name}')
            
            # Visualize augmentations
            print('\n[3] Generating augmentation examples...')
            
            pipeline.visualize_augmentations(sample_image, num_examples=4)
            
        else:
            print('No JPG files found in Apple___Apple_scab folder')
            
    else:
        print(f'Sample folder not found: {sample_image_path}')
    
    
    
    
        
# # IMAGEPROCESSOR class to handle image loading and preprocessing
# class ImageProcessor:
#     '''
#     Processes single images: read, augment, resize and save them in the specified output directory.
#     Tracks statistics (processed count, failed count) for monitoring and debugging.
#     '''
    
#     def __init__(self, augmentation_pipeline):
#         '''
#         Initialize processor with an augmentation pipeline.
#         Args:
#             augmentation_pipeline: AugmentationPipeline
#         '''
#         self.aug = augmentation_pipeline
#         self.stats = {'processed': 0, 'failed': 0}
#         print('ImageProcessor initialized')
        
#     # Read imag
#     def read_image(self, image_path):
#         '''
#         Read image from disk using opencv
#         Load image into memory as numpy array
#         Args: image_path: Path to the image file
#         Return image array if successful, None if failed
#         '''
        
#         img = cv2.imread(str(image_path)) # read image in BGR format
        
#         if img is None:
#             print(f'  Warning: Could not read {image_path.name}')
#             return None
        
#         # Convert BGR to RGB 
#         img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
#         return img
    
#     # Process the images
#     def process_image(self, image_path, output_dir, is_training=True):
#         '''
#         Process a single image: read -> augment -> save.
        
#         Args:
#             image_path (Path): Source image path
#             output_dir (Path): Destination directory
#             is_training (bool): Apply training augmentations if True
            
#         Returns:
#             bool: True if successful, False otherwise
#         '''
        
#         #1 Read the image
#         img = self.read_image(image_path) 
        
#         if img is None:
#             self.stats['failed'] += 1
#             return False
        
#         #2 Choose augmentation pipeline based on mode
#         if is_training:
#             pipeline = self.aug.get_train_pipeline()
        
#         else:
#             pipeline = self.aug.get_val_pipeline()
            
#         # 3: Apply augmentation
#         # pipeline(image=img) returns a dictionary with 'image' key
#         augmentad = pipeline(image=img)
#         processed_img = augmentad['image']
        
#         #4 Create output path
#         output_path = output_dir / image_path.name
        
#         #5 Save image
#         # Convert RGB back to BGR for OpenCV saving
#         processed_img_bgr = cv2.cvtColor(processed_img, cv2.COLOR_RGB2BGR)
#         cv2.imwrite(str(output_path), processed_img_bgr)
        
#         self.stats['processed'] += 1
#         return True
    
#     def get_stats(self):
#         '''
#         Return processing statistics dictionary.
#         '''
#         return self.stats.copy()
    
#     def reset_stats(self):
#         '''
#         Reset statistics to zero.
#         '''
#         self.stats = {'processed': 0, 'failed': 0}
        
        
# # Reset statistics to zero
# #Creates before/after comparison images for quality control

# class Visualizer:
#     '''
#     Visualizes original vs processed images.
    
#     Saves comparison charts to results folder 
#     '''
    
#     def __init__(self, save_dir):
#         '''
#         Initialize visualizer with save directory.
        
#         Args:
#             save_dir (Path): Directory to save visualization images
#         '''
        
#         self.save_dir = Path(save_dir)
#         self.save_dir.mkdir(parents=True, exist_ok=True)
        
#         print(f'Visualizer initialized. Saving to: {self.save_dir}')
        
        
#     def show_before_after(self, original, processed, class_name, image_name):
#         '''
#         Verify that augmentation is working correctly.
#         '''
        
#         # Create figure with 2 subplots side by side
#         fig, (ax1, ax2) = plt.subplot(1, 2, figsize=(10, 5))
        
#         # Plot original image
#         ax1.imshow(original)
#         ax1.set_title(f'Original\n{class_name}')
#         ax1.axis('off')
        
#         # Plot processes image
#         ax2.imshow(processed)
#         ax2.set_title(f'Processed (224x224)\n{class_name}')
#         ax2.axis('off')
        
#         #Add overall title
#         fig.suptitle(f'Before and After Processing', fontsize=14)
        
#         # Save the figure
#         safe_name = image_name.replace('.', '_')
#         save_path  = self.save_dir / f'{class_name}_{safe_name}.png'
#         plt.savefig(save_path, dpi=100, bbox_inches='tight')
#         plt.close(fig)
        
        
        
        
    
        
        
    
    