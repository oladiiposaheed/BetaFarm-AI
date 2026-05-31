# placeholder_model.py - Dummy model for testing API structure
import numpy as np

class PlaceholderModel:
    '''Placeholder model that returns random predictions for testing'''
    
    def predict(self, image):
        
        # Return random disease prediction (37 classes)
        # This simulates your real model while it's training
        random_class = np.random.randint(0, 38)
        confidence = np.random.uniform(0.5, 0.99)
        
        disease_names = [
            "Apple_scab", "Apple_black_rot", "Apple_cedar_rust", "Apple_healthy",
            "Blueberry_healthy", "Cherry_healthy", "Cherry_powdery_mildew",
            "Corn_cercospora", "Corn_common_rust", "Corn_northern_blight", "Corn_healthy",
            "Grape_black_rot", "Grape_esca", "Grape_leaf_blight", "Grape_healthy",
            "Orange_haunglongbing", "Peach_bacterial_spot", "Peach_healthy",
            "Pepper_bacterial_spot", "Pepper_healthy", "Potato_early_blight",
            "Potato_late_blight", "Potato_healthy", "Raspberry_healthy",
            "Soybean_healthy", "Squash_powdery_mildew", "Strawberry_healthy",
            "Strawberry_leaf_scorch", "Tomato_bacterial_spot", "Tomato_early_blight",
            "Tomato_late_blight", "Tomato_leaf_mold", "Tomato_septoria",
            "Tomato_spider_mites", "Tomato_target_spot", "Tomato_yellow_curl",
            "Tomato_mosaic_virus", "Tomato_healthy"
        ]
        
        return {
            'crop_name': 'Tomato',
            'disease_name': disease_names[random_class],
            'confidence': confidence,
            'health_status': 'unhealthy'
        }