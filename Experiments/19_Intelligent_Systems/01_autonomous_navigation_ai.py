#!/usr/bin/env python3
"""
Bab 19.1: Autonomous Navigation dengan AI Decision Making
==========================================================
Sistem navigasi otonom yang menggabungkan:
- Computer Vision (deteksi rintangan)
- Sensor fusion (ultrasonik + kamera)
- AI-based decision making
- Path planning

Hardware:
- Raspberry Pi 4/5
- Pi Camera
- Ultrasonik sensor (HC-SR04)
- Motor driver + DC motors
- Servo untuk pan/tilt kamera (optional)

Install:
  pip3 install opencv-python numpy gpiozero lgpio pillow
"""

import cv2
import numpy as np
import time
import threading
from datetime import datetime
from gpiozero import Motor, DistanceSensor, Servo
from gpiozero.pins.lgpio import LGPIOFactory

print("="*70)
print("Autonomous Navigation with AI Decision Making")
print("="*70)

# Set GPIO factory
try:
    from gpiozero import Device
    Device.pin_factory = LGPIOFactory()
except:
    pass

# ============================================================================
# ROBOT CONFIGURATION
# ============================================================================

# Motor pins
MOTOR_LEFT_FWD = 17
MOTOR_LEFT_BWD = 27
MOTOR_RIGHT_FWD = 23
MOTOR_RIGHT_BWD = 24

# Ultrasonic sensor pins
ULTRASONIC_TRIGGER = 5
ULTRASONIC_ECHO = 6

# Emergency stop distance (cm)
EMERGENCY_STOP_DISTANCE = 15
SAFE_DISTANCE = 30

# ============================================================================
# SENSOR FUSION CLASS
# ============================================================================

class SensorFusion:
    """Combine data from camera and ultrasonic sensors"""
    
    def __init__(self, camera_id=0):
        print("\n🔧 Initializing Sensor Fusion System...")
        
        # Camera
        self.camera = cv2.VideoCapture(camera_id)
        if not self.camera.isOpened():
            raise RuntimeError("Cannot open camera")
        
        # Ultrasonic sensor
        try:
            self.ultrasonic = DistanceSensor(
                echo=ULTRASONIC_ECHO,
                trigger=ULTRASONIC_TRIGGER,
                max_distance=4.0,
                threshold_distance=0.3
            )
        except:
            print("   ⚠️  Ultrasonic sensor not available (simulation mode)")
            self.ultrasonic = None
        
        # Sensor data
        self.current_distance = 100.0
        self.obstacle_detected_vision = False
        self.running = False
        
        print("✅ Sensor fusion system ready")
    
    def get_distance(self):
        """Get distance from ultrasonic sensor"""
        if self.ultrasonic:
            try:
                return self.ultrasonic.distance * 100  # Convert to cm
            except:
                return 100.0
        return 100.0
    
    def detect_obstacle_vision(self, frame):
        """Detect obstacles using computer vision"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Check bottom third of image for obstacles
        h, w = edges.shape
        roi = edges[int(h*0.6):h, :]
        
        # Count edge pixels
        edge_count = np.sum(roi > 0)
        total_pixels = roi.shape[0] * roi.shape[1]
        edge_ratio = edge_count / total_pixels
        
        # Obstacle detected if many edges (>15% of pixels)
        obstacle_detected = edge_ratio > 0.15
        
        return obstacle_detected, edge_ratio, edges
    
    def get_sensor_data(self):
        """Get fused sensor data"""
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        # Ultrasonic distance
        distance = self.get_distance()
        
        # Vision-based obstacle detection
        obstacle_vision, edge_ratio, edges = self.detect_obstacle_vision(frame)
        
        return {
            'frame': frame,
            'distance': distance,
            'obstacle_vision': obstacle_vision,
            'edge_ratio': edge_ratio,
            'edges': edges,
            'timestamp': time.time()
        }
    
    def close(self):
        """Release resources"""
        if self.camera:
            self.camera.release()

# ============================================================================
# AI DECISION MAKER
# ============================================================================

class AINavigationDecisionMaker:
    """AI-based decision making for autonomous navigation"""
    
    def __init__(self):
        print("\n🤖 Initializing AI Decision Maker...")
        
        # Decision history for learning
        self.decision_history = []
        self.obstacle_count = 0
        self.turn_preference = 0  # -1 = left, 1 = right, 0 = neutral
        
        print("✅ AI Decision Maker ready")
    
    def evaluate_situation(self, sensor_data):
        """Evaluate current situation and assign risk level"""
        distance = sensor_data['distance']
        obstacle_vision = sensor_data['obstacle_vision']
        
        # Risk scoring
        risk_score = 0
        
        # Distance-based risk
        if distance < EMERGENCY_STOP_DISTANCE:
            risk_score += 100
        elif distance < SAFE_DISTANCE:
            risk_score += 50
        elif distance < 50:
            risk_score += 20
        
        # Vision-based risk
        if obstacle_vision:
            risk_score += 30
        
        # Classify risk level
        if risk_score >= 100:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 20:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return risk_level, risk_score
    
    def make_decision(self, sensor_data):
        """Make navigation decision based on sensor data"""
        risk_level, risk_score = self.evaluate_situation(sensor_data)
        
        distance = sensor_data['distance']
        obstacle_vision = sensor_data['obstacle_vision']
        
        # Decision rules with AI logic
        decision = None
        reason = ""
        
        # CRITICAL: Emergency stop
        if risk_level == "CRITICAL":
            decision = "STOP"
            reason = f"Emergency stop - obstacle at {distance:.1f}cm"
            self.obstacle_count += 1
        
        # HIGH: Avoid obstacle
        elif risk_level == "HIGH":
            # Use learned turn preference
            if self.turn_preference < 0:
                decision = "TURN_LEFT"
                reason = "Avoiding obstacle - learned preference: LEFT"
            elif self.turn_preference > 0:
                decision = "TURN_RIGHT"
                reason = "Avoiding obstacle - learned preference: RIGHT"
            else:
                # Random choice, but remember it
                decision = np.random.choice(["TURN_LEFT", "TURN_RIGHT"])
                reason = "Avoiding obstacle - random choice"
                
                if decision == "TURN_LEFT":
                    self.turn_preference -= 1
                else:
                    self.turn_preference += 1
        
        # MEDIUM: Slow down
        elif risk_level == "MEDIUM":
            decision = "SLOW"
            reason = f"Caution - obstacle at {distance:.1f}cm"
        
        # LOW: Continue forward
        else:
            decision = "FORWARD"
            reason = "Path clear - moving forward"
        
        # Record decision
        self.decision_history.append({
            'timestamp': time.time(),
            'decision': decision,
            'reason': reason,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'distance': distance
        })
        
        # Keep only last 100 decisions
        if len(self.decision_history) > 100:
            self.decision_history.pop(0)
        
        return decision, reason, risk_level
    
    def get_statistics(self):
        """Get decision statistics"""
        if not self.decision_history:
            return None
        
        from collections import Counter
        decisions = [d['decision'] for d in self.decision_history]
        decision_counts = Counter(decisions)
        
        return {
            'total_decisions': len(self.decision_history),
            'obstacles_encountered': self.obstacle_count,
            'decision_distribution': dict(decision_counts),
            'turn_preference': 'LEFT' if self.turn_preference < -2 else 'RIGHT' if self.turn_preference > 2 else 'NEUTRAL'
        }

# ============================================================================
# ROBOT CONTROLLER
# ============================================================================

class AutonomousRobot:
    """Autonomous robot with AI navigation"""
    
    def __init__(self):
        print("\n🤖 Initializing Autonomous Robot...")
        
        # Motors
        try:
            self.motor_left = Motor(forward=MOTOR_LEFT_FWD, backward=MOTOR_LEFT_BWD)
            self.motor_right = Motor(forward=MOTOR_RIGHT_FWD, backward=MOTOR_RIGHT_BWD)
            self.motors_available = True
        except:
            print("   ⚠️  Motors not available (simulation mode)")
            self.motors_available = False
        
        # Components
        self.sensors = SensorFusion()
        self.ai = AINavigationDecisionMaker()
        
        # State
        self.running = False
        self.current_decision = "STOP"
        
        print("✅ Autonomous robot ready")
    
    def execute_decision(self, decision, speed=0.6):
        """Execute navigation decision"""
        if not self.motors_available:
            return
        
        if decision == "FORWARD":
            self.motor_left.forward(speed)
            self.motor_right.forward(speed)
        
        elif decision == "SLOW":
            self.motor_left.forward(speed * 0.4)
            self.motor_right.forward(speed * 0.4)
        
        elif decision == "TURN_LEFT":
            self.motor_left.backward(speed * 0.5)
            self.motor_right.forward(speed * 0.5)
        
        elif decision == "TURN_RIGHT":
            self.motor_left.forward(speed * 0.5)
            self.motor_right.backward(speed * 0.5)
        
        elif decision == "STOP":
            self.motor_left.stop()
            self.motor_right.stop()
    
    def run_autonomous(self, duration=60, display=True):
        """Run autonomous navigation"""
        print(f"\n🚀 Starting autonomous navigation for {duration}s...")
        print("   Press 'q' to stop")
        
        self.running = True
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < duration:
            # Get sensor data
            sensor_data = self.sensors.get_sensor_data()
            if sensor_data is None:
                continue
            
            # Make decision
            decision, reason, risk_level = self.ai.make_decision(sensor_data)
            
            # Execute decision
            self.execute_decision(decision)
            self.current_decision = decision
            
            # Display
            if display:
                frame = sensor_data['frame'].copy()
                h, w = frame.shape[:2]
                
                # Draw info overlay
                info_y = 30
                cv2.putText(frame, f"Decision: {decision}", (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                info_y += 30
                cv2.putText(frame, f"Risk: {risk_level}", (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                info_y += 30
                cv2.putText(frame, f"Distance: {sensor_data['distance']:.1f}cm", (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Draw edges overlay
                edges_colored = cv2.cvtColor(sensor_data['edges'], cv2.COLOR_GRAY2BGR)
                combined = np.hstack([frame, edges_colored])
                
                cv2.imshow('Autonomous Navigation (Press Q)', combined)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running = False
                    break
            
            time.sleep(0.1)
        
        # Stop motors
        self.execute_decision("STOP")
        
        if display:
            cv2.destroyAllWindows()
        
        # Print statistics
        stats = self.ai.get_statistics()
        if stats:
            print("\n📊 Navigation Statistics:")
            print(f"   Total decisions: {stats['total_decisions']}")
            print(f"   Obstacles encountered: {stats['obstacles_encountered']}")
            print(f"   Learned turn preference: {stats['turn_preference']}")
            print(f"   Decision distribution:")
            for decision, count in stats['decision_distribution'].items():
                print(f"      {decision}: {count}")
    
    def close(self):
        """Release all resources"""
        self.running = False
        if self.motors_available:
            self.motor_left.stop()
            self.motor_right.stop()
        self.sensors.close()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n💡 Autonomous Navigation with AI")
    print("   Sensor fusion + AI decision making")
    
    robot = None
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Initialize Robot")
        print("  2. Run Autonomous Navigation (30s)")
        print("  3. Run Autonomous Navigation (60s)")
        print("  4. Run Autonomous Navigation (Custom)")
        print("  5. Test Sensors Only")
        print("  6. View AI Statistics")
        print("  7. Shutdown Robot")
        print("  8. Exit")
        print("="*70)
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            robot = AutonomousRobot()
        
        elif choice == "2":
            if not robot:
                print("❌ Initialize robot first!")
                continue
            robot.run_autonomous(duration=30)
        
        elif choice == "3":
            if not robot:
                print("❌ Initialize robot first!")
                continue
            robot.run_autonomous(duration=60)
        
        elif choice == "4":
            if not robot:
                print("❌ Initialize robot first!")
                continue
            duration = input("Duration (seconds): ").strip()
            duration = int(duration) if duration.isdigit() else 30
            robot.run_autonomous(duration=duration)
        
        elif choice == "5":
            if not robot:
                print("❌ Initialize robot first!")
                continue
            
            print("\n📡 Testing sensors... (Press Ctrl+C to stop)")
            try:
                while True:
                    sensor_data = robot.sensors.get_sensor_data()
                    if sensor_data:
                        print(f"Distance: {sensor_data['distance']:.1f}cm | "
                              f"Vision obstacle: {sensor_data['obstacle_vision']} | "
                              f"Edge ratio: {sensor_data['edge_ratio']:.2f}", end='\r')
                    time.sleep(0.2)
            except KeyboardInterrupt:
                print("\n")
        
        elif choice == "6":
            if not robot:
                print("❌ Initialize robot first!")
                continue
            
            stats = robot.ai.get_statistics()
            if stats:
                print("\n📊 AI Decision Statistics:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
            else:
                print("   No data yet - run autonomous navigation first")
        
        elif choice == "7":
            if robot:
                robot.close()
                robot = None
                print("🛑 Robot shutdown complete")
        
        elif choice == "8":
            if robot:
                robot.close()
            break
    
    print("\n✅ Program finished!")
    print("\n🎓 What you learned:")
    print("  • Sensor fusion (vision + ultrasonic)")
    print("  • AI-based decision making")
    print("  • Risk assessment algorithms")
    print("  • Autonomous navigation")
    print("  • Adaptive learning (turn preference)")
    print("\n📖 Next: Bab 20 - Capstone Projects!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated")
        cv2.destroyAllWindows()
