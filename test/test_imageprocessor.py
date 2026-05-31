'''
Process individual images - read, augment, resize, save
'''

import cv2
from pathlib import Path
import matplotlib.pyplot as plt
import albumentations as A
from test.test_augmentation import AugmentationPipeline

# Create pipeline instance
pipeline = AugmentationPipeline(target_size=224)
print('Pipeline ready for use')


class ImageProcessor:
    '''
    Processes single images: read, augment, resize, save.
    
    Example:
        pipeline = AugmentationPipeline()
        processor = ImageProcessor(pipeline)
        processor.process_image("leaf.jpg", "output/", is_training=True)
        stats = processor.get_stats()  # {'processed': 1, 'failed': 0}
    '''
    
    def __init__(self, augmentation_pipeline):
        '''
        Initialize processor with augmentation pipeline.
        '''
        self.aug = augmentation_pipeline
        self.stats = {'processed': 0, 'failed': 0}
        
        print('ImageProcessor initialized')
        print('Statistics tracking started: processed=0, failed=0')
        
    def read_image(self, image_path):
        '''
        Reads image from path directory.
        
        Returns: numpy array (RGB) or None if failed
        '''
        img = cv2.imread(str(image_path))
        
        if img is None:
            print(f'Warning: Could not read: {image_path.name}')
            return None
        
        # Get original size for information
        h, w = img.shape[:2]
        print(f'Read: {image_path.name} ({w} x {h})')
        
        # Convert BGR to RGB (PyTorch expects RGB)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img
    
    def process_image(self, image_path, output_dir, is_training=True):
        '''
        Processes a single image: read -> augment -> save.
        
        Args:
            image_path: Source image path
            output_dir: Destination directory
            is_training: Apply training augmentations if True
        
        Returns:
            bool: True if successful, False otherwise
        '''
        # Read the image
        img = self.read_image(image_path)
        if img is None:
            self.stats['failed'] += 1
            return False
        
        # Choose augmentation based on mode
        if is_training:
            aug_pipeline = self.aug.get_train_pipeline()
            mode_text = 'TRAINING (with augmentations)'
        else:
            aug_pipeline = self.aug.get_val_pipeline()
            mode_text = 'VALIDATION (resize only)'
        
        print(f'Applying: {mode_text}')
        
        # Apply augmentation
        augmented = aug_pipeline(image=img)
        processed_img = augmented['image']
        
        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / image_path.name
        
        # Convert RGB back to BGR for OpenCV and save
        processed_img_bgr = cv2.cvtColor(processed_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output_path), processed_img_bgr)
        
        self.stats['processed'] += 1
        print(f'Saved to: {output_path.name}')
        return True
    
    def visualize_before_after(self, image_path, output_dir, is_training=True):
        '''
        Shows original vs processed image side by side.
        
        Args:
            image_path: Source image path
            output_dir: Destination directory (for processed image)
            is_training: Apply training augmentations
        '''
        print('\n🎨 Creating before/after visualization...')
        
        # Read original image
        original = self.read_image(image_path)
        if original is None:
            return
        
        # Get original size
        h_orig, w_orig = original.shape[:2]
        
        # Get plant name from parent folder
        plant_name = image_path.parent.name.replace('___', ' - ').replace('_', ' ')
        
        # Process the image (this saves it to output_dir)
        success = self.process_image(image_path, output_dir, is_training)  # FIXED: was * instead of (

        if not success:
            print(f'Failed to process {image_path.name}')
            return
        
        # Read the processed image back
        processed_path = output_dir / image_path.name
        processed = cv2.imread(str(processed_path))
        processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        h_proc, w_proc = processed.shape[:2]
        
        # Create side-by-side comparison
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Original image
        ax1.imshow(original)
        mode_text = 'TRAINING' if is_training else 'VALIDATION'
        ax1.set_title(f'BEFORE\n{plant_name}\n{w_orig}x{h_orig}', fontsize=11)
        ax1.axis('off')
        
        # Processed image
        ax2.imshow(processed)
        ax2.set_title(f'AFTER ({mode_text})\n{plant_name}\n{w_proc}x{h_proc}', fontsize=11)
        ax2.axis('off')
        
        plt.suptitle('Before vs After Image Processing', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save visualization
        viz_dir = Path(__file__).parent / 'results' / 'plots'
        viz_dir.mkdir(parents=True, exist_ok=True)
        save_path = viz_dir / f'before_after_{image_path.stem}.png'
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'\n💾 Visualization saved to: {save_path}')
        plt.show()
    
    def get_stats(self):
        '''Return processing statistics.'''
        return self.stats.copy()
    
    def reset_stats(self):
        '''Reset statistics to zero.'''
        self.stats = {'processed': 0, 'failed': 0}
        print('Statistics reset')


# ============================================================
# TEST THE IMAGEPROCESSOR
# ============================================================

if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('TESTING IMAGEPROCESSOR')
    print('=' * 60)
    
    # Create processor
    print('\n[1] Creating ImageProcessor...')
    processor = ImageProcessor(pipeline)
    
    # Find a sample image - FIXED: 'datasets' not 'dataset'
    train_path = Path(__file__).parent.parent / 'datasets' / 'new_plant_diseases' / 'train'
    
    print(f'\n[2] Looking for images in: {train_path}')
    
    if train_path.exists():
        class_folders = [f for f in train_path.iterdir() if f.is_dir()]
        
        if class_folders:
            sample_class = class_folders[0]
            print(f'\n    Using plant: {sample_class.name}')
            
            image_files = list(sample_class.glob('*.JPG')) + list(sample_class.glob('*.jpg'))
            
            if image_files:
                sample_image = image_files[0]
                print(f'    Image: {sample_image.name}')
                
                # Create output directory
                output_dir = Path(__file__).parent.parent / 'datasets' / 'new_plant_diseases' / 'processed' / 'train' / sample_class.name
                output_dir.mkdir(parents=True, exist_ok=True)
                print(f'\n[3] Output directory: {output_dir}')
                
                # Process and visualize
                print('\n[4] Processing image...')
                processor.visualize_before_after(sample_image, output_dir, is_training=True)
                
                # Show statistics
                print('\n[5] Processing statistics:')
                stats = processor.get_stats()
                print(f'    ✅ Processed: {stats["processed"]}')
                print(f'    ❌ Failed: {stats["failed"]}')
                
            else:
                print('    No images found')
        else:
            print('    No class folders found')
    else:
        print(f'❌ Train path not found: {train_path}')
        print('\n💡 Tip: Your dataset might be in a different location.')
        print('   Run this command to see where your dataset is:')
        print('   dir C:\\Users\\USER\\LLMOPs_Projects\\betafarm_ai\\datasets\\')