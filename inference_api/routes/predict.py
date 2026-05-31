'''
    Disease Prediction Endpoint
'''

import sys
from pathlib import Path
import numpy as np
from fastapi import APIRouter, File, UploadFile, HTTPException
sys.path.append(str(Path(__file__).parent.parent))
from services.preprocessing import preprocess_image
from services.model_loader import model_loader

router = APIRouter()

# DISEASE NAMES (38 classes)
DISEASE_NAMES = [
    'Apple Scab', 'Apple Black Rot', 'Apple Cedar Rust', 'Apple Healthy',
    'Blueberry Healthy', 'Cherry Powdery Mildew', 'Cherry Healthy',
    'Corn Cercospora Leaf Spot', 'Corn Common Rust', 'Corn Northern Leaf Blight', 'Corn Healthy',
    'Grape Black Rot', 'Grape Esca', 'Grape Leaf Blight', 'Grape Healthy',
    'Orange Huanglongbing', 'Peach Bacterial Spot', 'Peach Healthy',
    'Pepper Bacterial Spot', 'Pepper Healthy', 'Potato Early Blight', 'Potato Late Blight',
    'Potato Healthy', 'Raspberry Healthy', 'Soybean Healthy', 'Squash Powdery Mildew',
    'Strawberry Healthy', 'Strawberry Leaf Scorch', 'Tomato Bacterial Spot',
    'Tomato Early Blight', 'Tomato Late Blight', 'Tomato Leaf Mold', 'Tomato Septoria Leaf Spot',
    'Tomato Spider Mites', 'Tomato Target Spot', 'Tomato Yellow Leaf Curl',
    'Tomato Mosaic Virus', 'Tomato Healthy'
]

def softmax(x):
    """Convert logits to probabilities (0-1 range)"""
    # Subtract max for numerical stability
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

@router.post('/predict')
async def predict(image: UploadFile = File(...)):
    '''
    Predict plant disease from uploaded image.
    '''
    
    try:
        image_bytes = await image.read()
        
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail='Empty file')
        
        processed_image = preprocess_image(image_bytes)
        predictions = model_loader.predict(processed_image)
        
        # Get the first prediction (batch size 1)
        pred = predictions[0]
        
        # Apply softmax to get probabilities (0-1 range)
        probs = softmax(pred)
        
        predicted_class = int(np.argmax(probs))
        confidence = float(np.max(probs))
        
        if predicted_class < len(DISEASE_NAMES):
            disease_name = DISEASE_NAMES[predicted_class]
        else:
            disease_name = 'Unknown'
            
        if 'Healthy' in disease_name:
            health_status = 'Healthy'
        else:
            health_status = 'Unhealthy'
            
        return {
            'success': True,
            'predicted_class': predicted_class,
            'disease_name': disease_name,
            'confidence': round(confidence * 100, 2),
            'health_status': health_status
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f'Prediction error: {str(e)}'
        )