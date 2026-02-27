#!/usr/bin/env python3
"""
Bab 14: Test TFLite - Basic
============================
Program sederhana untuk test TensorFlow Lite inference

Install:
  pip3 install numpy pillow

Test dengan random image (tidak perlu download model)
"""

import numpy as np
import time

print("="*50)
print("Test TFLite - Basic")
print("="*50)

print("\n1. Testing NumPy...")
try:
    arr = np.random.rand(100, 100, 3)
    print(f"✅ Created array: {arr.shape}")
except Exception as e:
    print(f"❌ NumPy error: {e}")

print("\n2. Testing image processing...")
try:
    from PIL import Image
    
    img = Image.new('RGB', (224, 224), color='red')
    print(f"✅ Created image: {img.size}")
    
    img_array = np.array(img)
    print(f"✅ Image array: {img_array.shape}")
    
except Exception as e:
    print(f"❌ PIL error: {e}")

print("\n3. Testing TensorFlow Lite...")
try:
    import tflite_runtime.interpreter as tflite
    print("✅ TFLite runtime available")
except:
    try:
        import tensorflow.lite as tflite
        print("✅ TensorFlow Lite available")
    except:
        print("⚠️  TFLite not installed")
        print("   Install: pip3 install tflite-runtime")

print("\n4. Performance test...")
try:
    start = time.time()
    for i in range(100):
        _ = np.random.rand(224, 224, 3)
    elapsed = (time.time() - start) * 1000
    
    print(f"✅ 100 iterations: {elapsed:.1f}ms")
    print(f"   Average: {elapsed/100:.2f}ms per iteration")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Test selesai!")

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test library dan dependencies yang diperlukan untuk AI/ML inference
menggunakan TensorFlow Lite pada Raspberry Pi.

TensorFlow Lite:
TensorFlow Lite (TFLite) adalah versi lightweight dari TensorFlow yang dioptimasi untuk
mobile dan embedded devices seperti Raspberry Pi. Ukuran model lebih kecil dan inference
lebih cepat dibanding full TensorFlow.

Library yang Ditest:
1. NumPy:
   - Library fundamental untuk numerical computing di Python
   - Menyediakan array multi-dimensional dan mathematical operations
   - Digunakan untuk manipulasi image data (convert image ke array)
   - Test: create random array 100x100x3 (simulasi RGB image)

2. PIL (Pillow):
   - Python Imaging Library untuk image processing
   - Load, manipulate, dan save berbagai image formats
   - Convert antara image dan NumPy array
   - Test: create RGB image 224x224 (standard input size untuk banyak AI models)

3. TensorFlow Lite:
   - Runtime untuk execute TFLite models (.tflite files)
   - 2 options: tflite-runtime (lightweight) atau tensorflow.lite (full)
   - tflite-runtime lebih direkomendasikan untuk RPi (lebih kecil)
   - Test: check availability library

4. Performance:
   - Test kecepatan array creation (simulasi preprocessing)
   - 100 iterations create array 224x224x3
   - Measure execution time untuk estimate inference performance

Image Shape Convention:
- Grayscale: (height, width) atau (height, width, 1)
- RGB: (height, width, 3) dimana 3 = Red, Green, Blue channels
- Batch: (batch_size, height, width, channels)

Input Size 224x224:
Banyak pre-trained models (MobileNet, ResNet, etc) use 224x224 sebagai standard input.
Kenapa 224? Hasil dari evolution architecture (AlexNet era), balance antara accuracy
dan computational cost.

NumPy Array vs PIL Image:
- PIL Image: for image operations (resize, rotate, crop, filter)
- NumPy Array: for mathematical operations dan AI model input
- Conversion: np.array(pil_image) dan Image.fromarray(numpy_array)

Data Type:
- float32: untuk normalized data (0.0-1.0) - umum untuk neural networks
- uint8: untuk raw image data (0-255) - RGB values
- Model bisa require specific data type dan range

Preprocessing Pipeline (typical):
1. Load image dengan PIL
2. Resize ke target size (224x224)
3. Convert ke NumPy array
4. Normalize (divide by 255 untuk scale 0-1, atau standardize dengan mean/std)
5. Add batch dimension jika perlu
6. Feed ke model

Installation:
- NumPy: pip3 install numpy
- Pillow: pip3 install pillow  
- TFLite: pip3 install tflite-runtime (recommended) atau pip3 install tensorflow

Performance Considerations:
- Raspberry Pi 4: ~20-100ms per inference (depends on model)
- Model quantization (int8) bisa speed up 2-4x
- Use coral.ai USB accelerator untuk 10-20x speedup
"""
