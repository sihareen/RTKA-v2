#!/usr/bin/env python3
"""
Bab 14.2: TensorFlow Lite Hands-on - Image Classification
==========================================================
Praktik langsung inference dengan TensorFlow Lite:
- Load pre-trained model (MobileNetV2)
- Image classification
- Performance measurement
- Optimization demonstration

Install:
  pip3 install tensorflow pillow numpy

Download model (auto or manual):
  wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v1_1.0_224_quant.tflite
"""

import tensorflow as tf
import numpy as np
from PIL import Image
import time
import os
import urllib.request

# Model configuration
MODEL_URL = "https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v1_1.0_224_quant.tflite"
LABELS_URL = "https://storage.googleapis.com/download.tensorflow.org/models/tflite/mobilenet_v1_1.0_224_quant.txt"
MODEL_PATH = "mobilenet_v1_quant.tflite"
LABELS_PATH = "imagenet_labels.txt"

print("="*70)
print("TensorFlow Lite Hands-on - Image Classification")
print("="*70)

# ============================================================================
# MODEL & LABELS DOWNLOAD
# ============================================================================

def download_model():
    """Download TFLite model if not exists"""
    if not os.path.exists(MODEL_PATH):
        print(f"\n📥 Downloading model from TensorFlow Hub...")
        print(f"   URL: {MODEL_URL}")
        print(f"   Size: ~4MB (quantized INT8)")
        
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            print(f"✅ Model downloaded: {MODEL_PATH}")
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print("   Manual download:")
            print(f"   wget {MODEL_URL} -O {MODEL_PATH}")
            return False
    else:
        print(f"✅ Model found: {MODEL_PATH}")
    
    return True

def download_labels():
    """Download ImageNet labels"""
    if not os.path.exists(LABELS_PATH):
        print(f"\n📥 Downloading labels...")
        
        try:
            urllib.request.urlretrieve(LABELS_URL, LABELS_PATH)
            print(f"✅ Labels downloaded: {LABELS_PATH}")
        except:
            # Create basic labels
            print("⚠️  Using default labels")
            with open(LABELS_PATH, 'w') as f:
                for i in range(1001):
                    f.write(f"class_{i}\n")
    else:
        print(f"✅ Labels found: {LABELS_PATH}")
    
    return True

def load_labels():
    """Load ImageNet class labels"""
    with open(LABELS_PATH, 'r') as f:
        labels = [line.strip() for line in f.readlines()]
    return labels

# ============================================================================
# TFLITE INFERENCE
# ============================================================================

class TFLiteImageClassifier:
    """TensorFlow Lite Image Classifier"""
    
    def __init__(self, model_path):
        print(f"\n🔧 Loading TFLite model: {model_path}")
        
        # Load TFLite model
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        # Get input/output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Print model info
        self.print_model_info()
        
        print("✅ Model loaded successfully")
    
    def print_model_info(self):
        """Print model information"""
        print("\n📊 Model Information:")
        print(f"   Input shape:  {self.input_details[0]['shape']}")
        print(f"   Input dtype:  {self.input_details[0]['dtype']}")
        print(f"   Output shape: {self.output_details[0]['shape']}")
        print(f"   Output dtype: {self.output_details[0]['dtype']}")
        
        # Get quantization info
        if self.input_details[0]['dtype'] == np.uint8:
            print("   Quantization: INT8 (optimized) ✓")
        else:
            print("   Quantization: FP32 (full precision)")
    
    def preprocess_image(self, image_path):
        """Preprocess image for model input"""
        # Get input shape
        input_shape = self.input_details[0]['shape']
        height = input_shape[1]
        width = input_shape[2]
        
        # Load and resize image
        img = Image.open(image_path).convert('RGB')
        img = img.resize((width, height))
        
        # Convert to numpy array
        input_data = np.array(img, dtype=self.input_details[0]['dtype'])
        
        # Add batch dimension
        input_data = np.expand_dims(input_data, axis=0)
        
        return input_data
    
    def classify(self, image_path, top_k=5):
        """Classify image and return top-k predictions"""
        # Preprocess image
        input_data = self.preprocess_image(image_path)
        
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        
        # Run inference
        start_time = time.time()
        self.interpreter.invoke()
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Get output
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        output_data = output_data[0]  # Remove batch dimension
        
        # Get top-k predictions
        top_indices = np.argsort(output_data)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'index': int(idx),
                'confidence': float(output_data[idx]) / 255.0  # Normalize for quantized model
            })
        
        return results, inference_time

# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def create_test_image():
    """Create a test image if no image available"""
    test_image_path = "test_image.jpg"
    
    if not os.path.exists(test_image_path):
        print("\n📷 Creating test image (colored square)...")
        
        # Create 224x224 colored image
        img = Image.new('RGB', (224, 224))
        pixels = img.load()
        
        for i in range(224):
            for j in range(224):
                # Create gradient
                r = int(255 * i / 224)
                g = int(255 * j / 224)
                b = 128
                pixels[i, j] = (r, g, b)
        
        img.save(test_image_path)
        print(f"✅ Test image created: {test_image_path}")
    
    return test_image_path

def benchmark_performance(classifier, image_path, iterations=10):
    """Benchmark inference performance"""
    print(f"\n⏱️  Running benchmark ({iterations} iterations)...")
    
    inference_times = []
    
    for i in range(iterations):
        _, inference_time = classifier.classify(image_path, top_k=1)
        inference_times.append(inference_time)
        print(f"   Iteration {i+1}/{iterations}: {inference_time:.2f}ms", end='\r')
    
    print()  # New line
   
    avg_time = np.mean(inference_times)
    std_time = np.std(inference_times)
    fps = 1000 / avg_time
    
    print(f"\n📊 Benchmark Results:")
    print(f"   Average: {avg_time:.2f}ms")
    print(f"   Std Dev: {std_time:.2f}ms")
    print(f"   Min: {np.min(inference_times):.2f}ms")
    print(f"   Max: {np.max(inference_times):.2f}ms")
    print(f"   FPS: {fps:.1f} frames/second")
    
    if fps >= 30:
        print("   Performance: Excellent ✓✓")
    elif fps >= 15:
        print("   Performance: Good ✓")
    elif fps >= 5:
        print("   Performance: Acceptable")
    else:
        print("   Performance: Too slow ✗")

def demo_classification(classifier, labels, image_path):
    """Demo image classification"""
    print(f"\n🖼️  Classifying image: {image_path}")
    
    results, inference_time = classifier.classify(image_path, top_k=5)
    
    print(f"\n⏱️  Inference time: {inference_time:.2f}ms")
    print(f"📊 Top 5 predictions:")
    
    for i, result in enumerate(results):
        idx = result['index']
        conf = result['confidence']
        label = labels[idx] if idx < len(labels) else f"class_{idx}"
        
        # Create confidence bar
        bar_length = int(conf * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        
        print(f"   {i+1}. [{bar}] {conf*100:5.1f}% - {label}")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n💡 TensorFlow Lite Image Classification Demo")
    print("   Model: MobileNet V1 (quantized INT8)")
    print("   Dataset: ImageNet (1000 classes)")
    print()
    
    # Download model and labels
    if not download_model():
        return
    
    download_labels()
    labels = load_labels()
    
    # Load classifier
    classifier = TFLiteImageClassifier(MODEL_PATH)
    
    # Create test image if needed
    test_image = create_test_image()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Classify Test Image")
        print("  2. Classify Custom Image")
        print("  3. Run Performance Benchmark")
        print("  4. Show Model Details")
        print("  5. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            demo_classification(classifier, labels, test_image)
        
        elif choice == "2":
            image_path = input("Image path: ").strip()
            if os.path.exists(image_path):
                demo_classification(classifier, labels, image_path)
            else:
                print(f"❌ File not found: {image_path}")
        
        elif choice == "3":
            iterations = input("Number of iterations (default 10): ").strip()
            iterations = int(iterations) if iterations.isdigit() else 10
            benchmark_performance(classifier, test_image, iterations)
        
        elif choice == "4":
            classifier.print_model_info()
        
        elif choice == "5":
            break
        
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")
    print()
    print("🎓 What you learned:")
    print("  • Loading TFLite models")
    print("  • Image preprocessing")
    print("  • Running inference")
    print("  • Performance measurement")
    print("  • Quantized model benefits (INT8)")
    print()
    print("📖 Next: Bab 14.3 - Model Optimization Demo")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
