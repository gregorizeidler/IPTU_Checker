"""
TensorFlow/Keras based image analysis for land measurement
Provides deep learning alternative to OpenCV
"""

import os
import numpy as np

try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️  TensorFlow not installed. Install with: pip install tensorflow")

def load_segmentation_model(model_path=None):
    """
    Load a pre-trained segmentation model for land/building detection.
    
    Args:
        model_path (str): Path to custom model. If None, uses a simple model.
        
    Returns:
        keras.Model or None: Loaded model
    """
    if not TF_AVAILABLE:
        print("❌ TensorFlow not available")
        return None
    
    if model_path and os.path.exists(model_path):
        try:
            model = keras.models.load_model(model_path)
            print(f"✅ Loaded custom model from: {model_path}")
            return model
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return None
    else:
        # Create a simple U-Net-like model for segmentation
        print("📦 Creating default segmentation model...")
        return create_simple_segmentation_model()

def create_simple_segmentation_model(input_shape=(256, 256, 3)):
    """
    Create a simple segmentation model using Keras.
    
    Args:
        input_shape (tuple): Input image shape
        
    Returns:
        keras.Model: Compiled segmentation model
    """
    if not TF_AVAILABLE:
        return None
    
    inputs = keras.Input(shape=input_shape)
    
    # Encoder
    x = keras.layers.Conv2D(32, 3, activation='relu', padding='same')(inputs)
    x = keras.layers.MaxPooling2D(2)(x)
    
    x = keras.layers.Conv2D(64, 3, activation='relu', padding='same')(x)
    x = keras.layers.MaxPooling2D(2)(x)
    
    x = keras.layers.Conv2D(128, 3, activation='relu', padding='same')(x)
    x = keras.layers.MaxPooling2D(2)(x)
    
    # Decoder
    x = keras.layers.Conv2DTranspose(64, 3, strides=2, activation='relu', padding='same')(x)
    x = keras.layers.Conv2DTranspose(32, 3, strides=2, activation='relu', padding='same')(x)
    x = keras.layers.Conv2DTranspose(16, 3, strides=2, activation='relu', padding='same')(x)
    
    # Output layer
    outputs = keras.layers.Conv2D(1, 1, activation='sigmoid', padding='same')(x)
    
    model = keras.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    print("✅ Created simple segmentation model")
    return model

def preprocess_image_tf(image_path, target_size=(256, 256)):
    """
    Preprocess image for TensorFlow model.
    
    Args:
        image_path (str): Path to image
        target_size (tuple): Target size for model
        
    Returns:
        np.array: Preprocessed image
    """
    if not TF_AVAILABLE:
        return None
    
    try:
        # Load image
        img = keras.preprocessing.image.load_img(image_path, target_size=target_size)
        img_array = keras.preprocessing.image.img_to_array(img)
        img_array = img_array / 255.0  # Normalize to [0, 1]
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        
        return img_array
    except Exception as e:
        print(f"❌ Error preprocessing image: {e}")
        return None

def segment_land_tf(image_path, model=None, lat=None, lng=None):
    """
    Segment land/building areas using TensorFlow model.
    
    Args:
        image_path (str): Path to satellite image
        model (keras.Model): Segmentation model (optional)
        lat (float): Latitude for pixel-to-meter conversion
        lng (float): Longitude
        
    Returns:
        float: Estimated area in square meters
    """
    if not TF_AVAILABLE:
        print("❌ TensorFlow not available")
        return None
    
    print(f"🤖 Analyzing image with TensorFlow: {image_path}")
    
    # Load or create model
    if model is None:
        model = load_segmentation_model()
        if model is None:
            return None
    
    # Preprocess image
    img_array = preprocess_image_tf(image_path)
    if img_array is None:
        return None
    
    # Predict segmentation mask
    try:
        prediction = model.predict(img_array, verbose=0)
        mask = prediction[0, :, :, 0]
        
        # Threshold to binary mask
        binary_mask = (mask > 0.5).astype(np.uint8)
        
        # Count pixels in segmented area
        area_pixels = np.sum(binary_mask)
        total_pixels = binary_mask.shape[0] * binary_mask.shape[1]
        
        print(f"   📊 Segmented pixels: {area_pixels}/{total_pixels}")
        
        # Convert to square meters
        if lat is not None:
            import math
            zoom = 19
            base_meters_per_pixel = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
            area_m2 = area_pixels * (base_meters_per_pixel ** 2)
            
            print(f"   📐 Estimated area: {area_m2:.2f} m²")
            return round(area_m2, 2)
        else:
            # Return pixel count if no lat/lng
            return area_pixels
            
    except Exception as e:
        print(f"❌ Error in TensorFlow segmentation: {e}")
        return None

def train_custom_model(training_data_path, epochs=10, batch_size=8):
    """
    Train a custom segmentation model on your data.
    
    Args:
        training_data_path (str): Path to training data directory
        epochs (int): Number of training epochs
        batch_size (int): Batch size for training
        
    Returns:
        keras.Model: Trained model
    """
    if not TF_AVAILABLE:
        print("❌ TensorFlow not available")
        return None
    
    print(f"🎓 Training custom model...")
    print(f"   Data path: {training_data_path}")
    print(f"   Epochs: {epochs}, Batch size: {batch_size}")
    
    # This is a placeholder - you would need to implement data loading
    # and training loop based on your specific dataset format
    
    model = create_simple_segmentation_model()
    
    print("⚠️  Note: This is a placeholder. Implement custom training loop.")
    print("   You need:")
    print("   1. Images of satellite views")
    print("   2. Ground truth segmentation masks")
    print("   3. Data augmentation pipeline")
    
    return model

def analyze_with_pretrained_model(image_path, model_name='mobilenet'):
    """
    Use a pre-trained model for feature extraction.
    
    Args:
        image_path (str): Path to image
        model_name (str): 'mobilenet', 'resnet50', 'vgg16'
        
    Returns:
        np.array: Feature vector
    """
    if not TF_AVAILABLE:
        print("❌ TensorFlow not available")
        return None
    
    try:
        # Load pre-trained model
        if model_name == 'mobilenet':
            base_model = keras.applications.MobileNetV2(
                include_top=False, 
                weights='imagenet',
                pooling='avg'
            )
        elif model_name == 'resnet50':
            base_model = keras.applications.ResNet50(
                include_top=False,
                weights='imagenet',
                pooling='avg'
            )
        else:
            base_model = keras.applications.VGG16(
                include_top=False,
                weights='imagenet',
                pooling='avg'
            )
        
        # Preprocess image
        img = keras.preprocessing.image.load_img(image_path, target_size=(224, 224))
        img_array = keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = keras.applications.mobilenet_v2.preprocess_input(img_array)
        
        # Extract features
        features = base_model.predict(img_array, verbose=0)
        
        print(f"✅ Extracted features using {model_name}")
        return features
        
    except Exception as e:
        print(f"❌ Error with pre-trained model: {e}")
        return None

