'''
    ONNX Model Loader
    
    This file loads the trained AI model once and keeps it in memory.
    All prediction requests reuse the SAME loaded model.
'''

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import MODEL_PATH
import onnxruntime as ort #ONNX Runtime runs the model for predictions
import numpy as np

#Define ModelLoader Class
class ModelLoader:
    '''
    Singleton class that loads and serves the ONNX model.
    With Singleton:    Model loads once, all requests reuse it (FAST)
    '''
    
    # Class variable to store the single instance
    _instance = None
    
    def __new__(cls):
        '''
        Controls how new instances are created (Singleton logic).
        
        1. Check if an instance already exists (cls._instance)
        2. If NO instance exists: create one
        3. If instance EXISTS: return the existing one (don't create new)
        4. This guarantees only ONE instance ever exists
        
        RETURNS:
            The single instance of ModelLoader
        '''
        
        if cls._instance is None:
            # First time: create a new instance
            print('=' * 60)
            print('CREATING MODEL LOADER (FIRST AND ONLY TIME)')
            print('=' * 60)
            cls._instance = super().__new__(cls)
            
        return cls._instance
        # If instance already exists, returns the existing one
     
    # __init__: Initializes the instance (runs AFTER __new__)    
    def __init__(self):
        '''
        Initializes the model loader (only runs ONCE due to Singleton).
        1. Checks if already initialized
        2. If not, loads the model
        3. Sets _initialized = True so it won't load again
        '''
        
        # Check if already initialized (prevents double loading)
        if hasattr(self, '_initialized'):
            # Already loaded, skip initialization
            return
        
        # First time initialization
        self._initialized = True
        self._load_model()
        
    # Function to loads the ONNX model from disk
    def _load_model(self):
        '''
        Loads the ONNX model from disk into memory.
        
        STEPS:
            1. Check if model file exists
            2. Create ONNX Runtime session (to load model into memory)
            3. Get input layer details (name, shape)
            4. Get output layer details (name, shape)
            5. Store for later use in predict()
        '''
        
        print(f'\nLoading ONNX model from:')
        print(f'{MODEL_PATH}')
        
        # Check if model file exists on disk
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f'\nModel not found at: {MODEL_PATH}\n')
        
        # Create ONNX Runtime session with CPU provider
        self.session = ort.InferenceSession(
            str(MODEL_PATH),
            providers=['CPUExecutionProvider'] # Use CPU for inference
        )

        # Get input layer information
        # Input layer: where we feed the image data
        self.input_name = self.session.get_inputs()[0].name
        input_shape = self.session.get_inputs()[0].shape
        
        print('INPUT LAYER:')
        print(f'Name: {self.input_name}')
        print(f'Shape: {input_shape}')
        print('Meaning: (batch_size, channels, height, width)')
        
        # Get output layer information
        # Output layer: where predictions come out
        self.output_name = self.session.get_outputs()[0].name
        output_shape = self.session.get_outputs()[0].shape
        
        print('OUTPUT LAYER:')
        print(f'Name: {self.output_name}')
        print(f'Shape: {output_shape}')
        print(f'Meaning: (batch_size, 38 disease probabilities)')
        
        print('Model loaded successfully and ready for predictions!')
        print('=' * 60)
        
    # predict: Runs inference on preprocessed image
    def predict(self, image_array):
        '''
        Run inference on a preprocessed image.
        Work:
            1. Takes preprocessed image (shape: 1, 3, 224, 224)
            2. Feeds it to the ONNX model
            3. Returns probabilities for 38 diseases
        '''
        
        outputs = self.session.run(
            [self.output_name],
            {self.input_name: image_array.astype(np.float32)}
        )    
        
        return outputs[0]
        
        
model_loader = ModelLoader()

print('ModelLoader is ready!')
print('= '* 60)