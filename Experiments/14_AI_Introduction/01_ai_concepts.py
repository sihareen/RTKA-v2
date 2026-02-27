#!/usr/bin/env python3
"""
Bab 14.1: AI Concepts - Understanding AI, ML, and Deep Learning
================================================================
Pengenalan konsep AI, ML, Deep Learning untuk Edge Computing

Topics:
1. AI vs ML vs Deep Learning (definitions & relationships)
2. Edge AI vs Cloud AI (comparison)
3. Hardware considerations untuk Raspberry Pi
4. Model optimization techniques
5. TensorFlow Lite introduction

This is theoretical foundation - no hardware needed
"""

import sys
import time
from datetime import datetime

print("="*70)
print("AI Concepts - Artificial Intelligence pada Raspberry Pi")
print("="*70)

# ============================================================================
# AI/ML/DL CONCEPTS
# ============================================================================

def explain_ai_hierarchy():
    """Explain relationship between AI, ML, and Deep Learning"""
    print("\n" + "="*70)
    print("1. AI / ML / Deep Learning Hierarchy")
    print("="*70)
    
    hierarchy = """
    ┌─────────────────────────────────────────────────────────┐
    │  ARTIFICIAL INTELLIGENCE (AI)                           │
    │  Komputer yang dapat "berpikir" seperti manusia         │
    │                                                          │
    │  ┌────────────────────────────────────────────────────┐ │
    │  │  MACHINE LEARNING (ML)                             │ │
    │  │  Sistem yang belajar dari data                     │ │
    │  │                                                     │ │
    │  │  ┌──────────────────────────────────────────────┐ │ │
    │  │  │  DEEP LEARNING (DL)                          │ │ │
    │  │  │  ML menggunakan Neural Networks              │ │ │
    │  │  │                                               │ │ │
    │  │  │  Examples:                                    │ │ │
    │  │  │  • CNN (Image Recognition)                   │ │ │
    │  │  │  • RNN (Sequential Data)                     │ │ │
    │  │  │  • Transformer (NLP)                         │ │ │
    │  │  └──────────────────────────────────────────────┘ │ │
    │  │                                                     │ │
    │  │  Other ML: Decision Trees, SVM, Random Forest      │ │
    │  └────────────────────────────────────────────────────┘ │
    │                                                          │
    │  Other AI: Expert Systems, Rule-based, Search           │
    └─────────────────────────────────────────────────────────┘
    """
    
    print(hierarchy)
    
    print("\nDefinitions:")
    print("  • AI: Broad field of making machines 'intelligent'")
    print("  • ML: Subset of AI that learns from data")
    print("  • DL: Subset of ML using neural networks (layers)")
    
    print("\nExamples untuk Robot:")
    print("  Rule-based (AI):    IF distance < 20cm THEN stop")
    print("  ML:                 Learn optimal speed from sensor data")
    print("  Deep Learning:      Recognize objects with camera (CNN)")

def explain_edge_vs_cloud():
    """Explain Edge AI vs Cloud AI"""
    print("\n" + "="*70)
    print("2. Edge AI vs Cloud AI")
    print("="*70)
    
    comparison = """
    ┌────────────────┬─────────────────────┬─────────────────────┐
    │   Feature      │     Edge AI         │     Cloud AI        │
    │                │  (Raspberry Pi)     │   (AWS, Google)     │
    ├────────────────┼─────────────────────┼─────────────────────┤
    │ Processing     │ Local device        │ Remote server       │
    │ Latency        │ <100ms (fast)       │ 200-1000ms          │
    │ Internet       │ Not required        │ Required            │
    │ Privacy        │ High (data local)   │ Lower               │
    │ Power          │ Low (2-5W)          │ High (kW)           │
    │ Cost           │ One-time HW         │ Subscription        │
    │ Model Size     │ Limited (<100MB)    │ Unlimited (GB)      │
    │ Accuracy       │ Good                │ Excellent           │
    │ Scalability    │ Per device          │ Centralized         │
    └────────────────┴─────────────────────┴─────────────────────┘
    
    Edge AI Benefits:
    ✓ Real-time response (critical untuk robot)
    ✓ Works offline
    ✓ Privacy-first (data tidak upload)
    ✓ Lower operational cost
    
    Edge AI Challenges:
    ✗ Limited compute power
    ✗ Smaller models (lower accuracy)
    ✗ Memory constraints
    ✗ Thermal management
    
    Best Practice: Hybrid Approach
    • Edge: Real-time inference (object detection, navigation)
    • Cloud: Model training, analytics, updates
    """
    
    print(comparison)
    
    print("\nRaspberry Pi sebagai Edge Device:")
    print("  ✓ CPU: 4 cores @ 1.5-2.4 GHz")
    print("  ✓ RAM: 2-8 GB")
    print("  ✓ GPU: VideoCore (basic acceleration)")
    print("  ⚠  No dedicated AI accelerator (unless Coral TPU)")

def explain_raspberry_pi_limitations():
    """Explain hardware limitations and optimizations"""
    print("\n" + "="*70)
    print("3. Raspberry Pi Hardware Considerations")
    print("="*70)
    
    limitations = """
    Hardware Limitations:
    
    1. CPU Performance:
       • 4 cores @ 1.5 GHz (Pi 4) or 2.4 GHz (Pi 5)
       • ARM architecture (not x86)
       • ~10-20x slower than modern laptop CPU
       
    2. Memory (RAM):
       • 2GB: Basic AI tasks
       • 4GB: Recommended for CV
       • 8GB: Best for complex models
       • No swap to SSD (SD card is slow)
       
    3. No Dedicated GPU:
       • VideoCore GPU: Limited for AI
       • No CUDA support (NVIDIA only)
       • CPU-only inference
       
    4. Thermal Throttling:
       • CPU throttles at ~80°C
       • Sustained load → performance drop
       • Cooling required for AI workloads
       
    5. Storage:
       • SD Card: Slow I/O
       • Model loading time: seconds
       • Limited to ~64GB typically
    """
    
    print(limitations)
    
    print("\nWorkarounds & Optimizations:")
    print("  1. Use quantized models (INT8 vs FP32)")
    print("  2. Reduce input resolution (320x240 vs 1920x1080)")
    print("  3. Lower frame rate (10 FPS vs 30 FPS)")
    print("  4. TensorFlow Lite (optimized for mobile/edge)")
    print("  5. Model pruning & distillation")
    print("  6. Google Coral TPU (40x faster inference)")
    print("  7. Active cooling (fan + heatsink)")
    print("  8. Overclock CPU (with cooling)")

def explain_model_optimization():
    """Explain model optimization techniques"""
    print("\n" + "="*70)
    print("4. Model Optimization Techniques")
    print("="*70)
    
    optimization = """
    Why Optimize?
    • Full model: 100MB, 500ms inference → Too slow
    • Optimized: 5MB, 50ms inference → Usable!
    
    Optimization Techniques:
    
    1. Quantization (INT8):
       • Convert FP32 (32-bit) → INT8 (8-bit)
       • 4x smaller model size
       • 2-4x faster inference
       • Minimal accuracy loss (<1%)
       
       Example:
       Weight: 3.14159265 (FP32) → 3 (INT8)
       
    2. Pruning:
       • Remove unnecessary neurons/connections
       • 50-90% size reduction
       • Maintain accuracy
       
    3. Knowledge Distillation:
       • Large "teacher" model trains small "student"
       • Student mimics teacher behavior
       • 10-100x smaller, similar accuracy
       
    4. Neural Architecture Search (NAS):
       • Auto-design efficient networks
       • MobileNet, EfficientNet (from NAS)
       
    5. Model Conversion:
       • TensorFlow → TensorFlow Lite (.tflite)
       • PyTorch → ONNX → TFLite
       • Keras → TFLite
    
    6. Input Resolution:
       • 1920x1080 → 320x240 (7.7x fewer pixels!)
       • Faster preprocessing & inference
       
    7. Batch Size = 1:
       • Process one image at a time
       • Lower latency (important for robot)
    """
    
    print(optimization)
    
    print("\nModel Size Comparison:")
    print("  ResNet50 (full):      98 MB  | 800ms inference")
    print("  MobileNetV2:          14 MB  | 150ms inference")
    print("  MobileNetV2 (quant):   3.5MB |  50ms inference ✓")
    
    print("\nBest for Raspberry Pi:")
    print("  • MobileNet SSD (object detection)")
    print("  • EfficientNet-Lite (image classification)")
    print("  • YOLO-Tiny (fast object detection)")
    print("  • MediaPipe (hand/pose detection)")

def explain_tflite():
    """Explain TensorFlow Lite"""
    print("\n" + "="*70)
    print("5. TensorFlow Lite Introduction")
    print("="*70)
    
    tflite_info = """
    TensorFlow Lite (TFLite):
    • Optimized ML framework untuk edge devices
    • Cross-platform: Android, iOS, Raspberry Pi, MCU
    • Smaller runtime (~1MB vs ~500MB TensorFlow)
    • Hardware acceleration support
    
    TFLite Architecture:
    
    ┌──────────────────────────────────────────────────┐
    │  Model Training (PC/Cloud)                       │
    │  • TensorFlow/Keras                              │
    │  • Train on large dataset                        │
    │  • Model: model.h5 or model.pb                   │
    └───────────────┬──────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────────────┐
    │  Conversion (TFLite Converter)                   │
    │  • Quantize (FP32 → INT8)                        │
    │  • Optimize operations                           │
    │  • Output: model.tflite                          │
    └───────────────┬──────────────────────────────────┘
                    │
                    ▼
    ┌──────────────────────────────────────────────────┐
    │  Deployment (Raspberry Pi)                       │
    │  • TFLite Interpreter                            │
    │  • Load model.tflite                             │
    │  • Run inference                                 │
    └──────────────────────────────────────────────────┘
    
    TFLite Components:
    1. Interpreter: Runs .tflite models
    2. Delegates: Hardware acceleration (GPU, NPU, Coral TPU)
    3. Ops: Optimized operations (Conv2D, MatMul, etc)
    
    Code Example:
    ```python
    import tensorflow as tf
    
    # Load TFLite model
    interpreter = tf.lite.Interpreter(model_path="model.tflite")
    interpreter.allocate_tensors()
    
    # Get input/output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Run inference
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]['index'])
    ```
    
    Supported Models:
    ✓ Image Classification (MobileNet, EfficientNet)
    ✓ Object Detection (SSD, YOLO)
    ✓ Segmentation (DeepLab)
    ✓ Pose Estimation (PoseNet)
    ✓ Custom models
    """
    
    print(tflite_info)

def show_performance_benchmarks():
    """Show real-world performance benchmarks"""
    print("\n" + "="*70)
    print("6. Performance Benchmarks (Raspberry Pi 4, 4GB)")
    print("="*70)
    
    benchmarks = """
    Model Inference Time:
    
    Image Classification:
    • MobileNetV2 (FP32):        150ms  (~6 FPS)
    • MobileNetV2 (INT8):         50ms  (~20 FPS) ✓
    • EfficientNet-LiteB0:        80ms  (~12 FPS)
    
    Object Detection:
    • SSD MobileNetV2 (FP32):    300ms  (~3 FPS)
    • SSD MobileNetV2 (INT8):    120ms  (~8 FPS) ✓
    • YOLO v3 (full):           2000ms  (~0.5 FPS) ✗
    • YOLO v3 Tiny:              250ms  (~4 FPS)
    • YOLO v5 Nano (INT8):       100ms  (~10 FPS) ✓
    
    Pose Estimation:
    • PoseNet (MobileNet):       200ms  (~5 FPS)
    • MediaPipe Pose:            150ms  (~6 FPS)
    
    Face Detection:
    • Haar Cascade (OpenCV):      20ms  (~50 FPS) ✓✓
    • DNN (Caffe):               100ms  (~10 FPS)
    • MediaPipe Face:             80ms  (~12 FPS)
    
    Note: FPS = Frames Per Second (higher is better)
           ✓ = Usable for robot applications
           ✓✓ = Excellent performance
           ✗ = Too slow for real-time
    
    With Google Coral TPU:
    • Object Detection:           20ms  (~50 FPS) ✓✓
    • Image Classification:       5ms   (~200 FPS)
    """
    
    print(benchmarks)
    
    print("\nRecommendations:")
    print("  Real-time robot (30 FPS):  Haar Cascade, lite models")
    print("  Good robot (10-15 FPS):    MobileNet INT8, MediaPipe")
    print("  Acceptable (5-10 FPS):     SSD, YOLO Tiny")
    print("  Research only (<5 FPS):    Large YOLO, ResNet")

# ============================================================================
# INTERACTIVE MENU
# ============================================================================

def main():
    print("\n📚 AI Concepts Tutorial")
    print("   Memahami AI untuk Raspberry Pi")
    print()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. AI / ML / Deep Learning Hierarchy")
        print("  2. Edge AI vs Cloud AI")
        print("  3. Raspberry Pi Hardware Limitations")
        print("  4. Model Optimization Techniques")
        print("  5. TensorFlow Lite Introduction")
        print("  6. Performance Benchmarks")
        print("  7. Show All (Complete Tutorial)")
        print("  8. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            explain_ai_hierarchy()
        
        elif choice == "2":
            explain_edge_vs_cloud()
        
        elif choice == "3":
            explain_raspberry_pi_limitations()
        
        elif choice == "4":
            explain_model_optimization()
        
        elif choice == "5":
            explain_tflite()
        
        elif choice == "6":
            show_performance_benchmarks()
        
        elif choice == "7":
            explain_ai_hierarchy()
            time.sleep(2)
            explain_edge_vs_cloud()
            time.sleep(2)
            explain_raspberry_pi_limitations()
            time.sleep(2)
            explain_model_optimization()
            time.sleep(2)
            explain_tflite()
            time.sleep(2)
            show_performance_benchmarks()
        
        elif choice == "8":
            break
        
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Tutorial selesai!")
    print()
    print("🎓 Key Takeaways:")
    print("  • AI ⊃ ML ⊃ Deep Learning (hierarchy)")
    print("  • Edge AI: Fast, private, offline (good for robots)")
    print("  • Raspberry Pi: Limited hardware (need optimization)")
    print("  • TensorFlow Lite: Best framework untuk edge")
    print("  • Quantization: 4x smaller, 2-4x faster")
    print("  • Target: 10-20 FPS untuk robot real-time")
    print()
    print("📖 Next: Bab 14.2 - TensorFlow Lite Hands-on")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan")
