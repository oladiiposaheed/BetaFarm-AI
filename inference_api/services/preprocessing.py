'''
    Image Preprocessing for Model Input.
    Converts raw uploaded images into the format expected by the model.
         The model expects: (1, 3, 224, 224) normalized tensor
         What this file does:
            1. Takes image bytes (from uploaded file)
            2. Decodes to image
            3. Resizes to 224x224
            4. Converts BGR to RGB
            5. Normalizes pixel values
            6. Adds batch dimension
            7. Returns ready-to-use numpy array
'''

import sys
from pathlib import Path
import numpy as np
import cv2
# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
from config import IMAGE_SIZE, IMAGE_MEAN, IMAGE_STD

def preprocess_image(image_bytes):
    '''
        Convert raw image bytes to model input format
        np.frombuffer: Converts bytes to numpy array
        RETURNS:
            numpy array of shape (1, 3, 224, 224) ready for model input
    '''
    
    # Decode image bytes to numpy array
    np_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    
    # Check if image was decoded successfully
    if img is None:
        raise ValueError('Could not decode image. File may be corrupted or not an image.')
    
    # Resize to 224x224 (MobileNet input size)
    img = cv2.resize(img, IMAGE_SIZE)
    
    # Convert BGR to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # cv2(BGR)->pytorch(RGB)
    
    #Convert to float and normalize to [0, 1]
    img = img.astype(np.float32) / 255.0 # original pixel[(0-255)]->(0.0-1.0)
    
    #Normalize using ImageNet mean and std
    for i in range(3): #loop RGB channel
        img[:, :, i] = (img[:, :, i]) - IMAGE_MEAN[i] / IMAGE_STD[i]
        
    #Change shape from (H, W, C) to (C, H, W)
    img = np.transpose(img, (2, 0, 1))
    
    #Add batch dimension
    img = np.expand_dims(img, axis=0)
    
    return img


if __name__=='__main__':
    print('Testing preprocess_image function...')
    print('Create a dummy image for testing')
    
    # Create a small test image (100x100 black image)
    test_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    
    print("Note: This test requires a real image file to work properly.")
    print("Use this function in the main app with real uploaded images.")

    