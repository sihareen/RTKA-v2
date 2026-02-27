#!/usr/bin/env python3
"""
Bab 12 Mini Project #1: Autonomous Obstacle Avoidance Robot
============================================================
Robot otonom yang bisa menghindari halangan dengan:
1. State machine untuk decision making
2. Multi-zone obstacle detection
3. Smart navigation algoritm
4. Safety features
5. Logging & monitoring

Hardware:
- HC-SR04 Ultrasonic sensor (Trigger=26, Echo=20)
- Motor DC 4WD dengan L298N
- LED status indicator
- Buzzer untuk peringatan
"""

from gpiozero import Robot, DistanceSensor, LED, Buzzer
from gpiozero.pins.lgpio import LGPIOFactory
from enum import Enum
import time
from datetime import datetime

# Setup pin factory for Raspberry Pi 5
factory = LGPIOFactory()

# Hardware setup
robot = Robot(left=(22, 27), right=(17, 18), pin_factory=factory)
sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0, pin_factory=factory)
status_led = LED(7, pin_factory=factory)
buzzer = Buzzer(4, pin_factory=factory)

# Configuration
class Config:
    # Distance thresholds (in cm)
    STOP_DISTANCE = 15      # Emergency stop
    SLOW_DISTANCE = 30      # Start slowing down
    SAFE_DISTANCE = 50      # Normal operation
    
    # Speeds
    NORMAL_SPEED = 0.7
    SLOW_SPEED = 0.4
    TURN_SPEED = 0.6
    
    # Timing
    SCAN_INTERVAL = 0.1     # Sensor reading interval
    TURN_DURATION = 0.8     # Time to turn ~90 degrees
    BACKUP_DURATION = 0.5   # Time to back up
    
    # Modes
    DEBUG = True            # Print debug messages
    SAFE_MODE = True        # Enable safety features

# State machine
class RobotState(Enum):
    IDLE = "idle"
    MOVING_FORWARD = "moving_forward"
    SLOWING_DOWN = "slowing_down"
    OBSTACLE_DETECTED = "obstacle_detected"
    BACKING_UP = "backing_up"
    TURNING = "turning"
    SCANNING = "scanning"
    ERROR = "error"

class AutonomousRobot:
    """Autonomous robot with obstacle avoidance"""
    
    def __init__(self):
        self.state = RobotState.IDLE
        self.running = False
        self.distance = 0
        self.turn_direction = "right"  # Default turn direction
        self.stats = {
            'total_distance_checks': 0,
            'obstacles_avoided': 0,
            'turns_made': 0,
            'backup_count': 0,
            'run_time': 0
        }
        self.start_time = None
    
    def log(self, message):
        """Log message with timestamp"""
        if Config.DEBUG:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] {message}")
    
    def get_distance(self):
        """Get distance from sensor with error handling"""
        try:
            distance_m = sensor.distance
            distance_cm = distance_m * 100
            
            # Filter unrealistic readings
            if distance_cm > 400 or distance_cm < 2:
                return self.distance  # Return last known good value
            
            self.distance = distance_cm
            self.stats['total_distance_checks'] += 1
            
            return distance_cm
        
        except Exception as e:
            self.log(f"⚠️  Sensor error: {e}")
            return self.distance
    
    def set_state(self, new_state):
        """Change robot state"""
        if new_state != self.state:
            self.log(f"State: {self.state.value} -> {new_state.value}")
            self.state = new_state
    
    def emergency_stop(self):
        """Emergency stop with warning"""
        robot.stop()
        status_led.on()
        buzzer.beep(on_time=0.1, n=3, background=True)
        self.log("🚨 EMERGENCY STOP")
    
    def move_forward(self, speed=Config.NORMAL_SPEED):
        """Move forward with speed control"""
        robot.forward(speed)
        status_led.on()
        self.set_state(RobotState.MOVING_FORWARD)
    
    def slow_down(self):
        """Gradually slow down"""
        robot.forward(Config.SLOW_SPEED)
        status_led.blink(on_time=0.1, off_time=0.1)
        self.set_state(RobotState.SLOWING_DOWN)
    
    def backup(self):
        """Back up from obstacle"""
        self.log("⬅️  Backing up...")
        robot.backward(Config.NORMAL_SPEED)
        status_led.blink(on_time=0.05, off_time=0.05)
        
        time.sleep(Config.BACKUP_DURATION)
        robot.stop()
        
        self.stats['backup_count'] += 1
        self.set_state(RobotState.BACKING_UP)
    
    def turn(self, direction=None):
        """Turn to avoid obstacle"""
        if direction is None:
            direction = self.turn_direction
        
        self.log(f"↻  Turning {direction}...")
        
        if direction == "right":
            robot.right(Config.TURN_SPEED)
        else:
            robot.left(Config.TURN_SPEED)
        
        status_led.blink(on_time=0.2, off_time=0.2)
        
        time.sleep(Config.TURN_DURATION)
        robot.stop()
        
        self.stats['turns_made'] += 1
        self.set_state(RobotState.TURNING)
        
        # Alternate turn direction for next time
        self.turn_direction = "left" if direction == "right" else "right"
    
    def scan_environment(self):
        """Scan environment to find best path"""
        self.log("👁️  Scanning environment...")
        self.set_state(RobotState.SCANNING)
        
        distances = {
            'center': self.get_distance(),
            'right': 0,
            'left': 0
        }
        
        # Look right
        robot.right(Config.TURN_SPEED)
        time.sleep(0.3)
        robot.stop()
        time.sleep(0.1)
        distances['right'] = self.get_distance()
        
        # Look left (need to turn back then left)
        robot.left(Config.TURN_SPEED)
        time.sleep(0.6)
        robot.stop()
        time.sleep(0.1)
        distances['left'] = self.get_distance()
        
        # Return to center
        robot.right(Config.TURN_SPEED)
        time.sleep(0.3)
        robot.stop()
        
        self.log(f"   Distances - L:{distances['left']:.1f} C:{distances['center']:.1f} R:{distances['right']:.1f}")
        
        # Decide best direction
        if distances['left'] > distances['right'] and distances['left'] > Config.SAFE_DISTANCE:
            return 'left'
        elif distances['right'] > Config.SAFE_DISTANCE:
            return 'right'
        else:
            return 'left'  # Default if both blocked
    
    def navigate(self):
        """Main navigation logic"""
        distance = self.get_distance()
        
        # Emergency stop zone
        if distance < Config.STOP_DISTANCE:
            if self.state != RobotState.OBSTACLE_DETECTED:
                self.emergency_stop()
                self.set_state(RobotState.OBSTACLE_DETECTED)
                self.stats['obstacles_avoided'] += 1
                
                # Decide what to do
                self.backup()
                best_direction = self.scan_environment()
                self.turn(best_direction)
        
        # Slow down zone
        elif distance < Config.SLOW_DISTANCE:
            if self.state not in [RobotState.SLOWING_DOWN, RobotState.OBSTACLE_DETECTED]:
                self.slow_down()
        
        # Caution zone
        elif distance < Config.SAFE_DISTANCE:
            if self.state == RobotState.MOVING_FORWARD:
                self.slow_down()
        
        # Safe zone - full speed ahead
        else:
            if self.state != RobotState.MOVING_FORWARD:
                self.move_forward()
    
    def run(self, duration=None):
        """Main run loop"""
        self.running = True
        self.start_time = time.time()
        
        print("\n" + "="*70)
        print("🤖 Autonomous Obstacle Avoidance Robot")
        print("="*70)
        print("\nConfiguration:")
        print(f"  Stop Distance: {Config.STOP_DISTANCE} cm")
        print(f"  Slow Distance: {Config.SLOW_DISTANCE} cm")
        print(f"  Safe Distance: {Config.SAFE_DISTANCE} cm")
        print(f"  Normal Speed: {Config.NORMAL_SPEED * 100}%")
        print()
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while self.running:
                # Check if duration limit reached
                if duration and (time.time() - self.start_time) > duration:
                    self.log(f"⏱️  Duration limit reached ({duration}s)")
                    break
                
                # Main navigation
                self.navigate()
                
                # Update stats
                self.stats['run_time'] = time.time() - self.start_time
                
                # Small delay
                time.sleep(Config.SCAN_INTERVAL)
        
        except KeyboardInterrupt:
            self.log("\n⏸️  Stopped by user")
        
        finally:
            self.stop()
            self.print_stats()
    
    def stop(self):
        """Stop robot and cleanup"""
        self.running = False
        robot.stop()
        status_led.off()
        buzzer.off()
        self.set_state(RobotState.IDLE)
    
    def print_stats(self):
        """Print run statistics"""
        print("\n" + "="*70)
        print("📊 Run Statistics")
        print("="*70)
        print(f"Run Time: {self.stats['run_time']:.1f} seconds")
        print(f"Distance Checks: {self.stats['total_distance_checks']}")
        print(f"Obstacles Avoided: {self.stats['obstacles_avoided']}")
        print(f"Turns Made: {self.stats['turns_made']}")
        print(f"Backups: {self.stats['backup_count']}")
        
        # Calculate efficiency
        if self.stats['run_time'] > 0:
            avg_check_rate = self.stats['total_distance_checks'] / self.stats['run_time']
            print(f"Avg Check Rate: {avg_check_rate:.1f} checks/sec")
        
        print("="*70)

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n🤖 Autonomous Obstacle Avoidance Robot")
    print("="*70)
    print("\nThis robot will:")
    print("  ✓ Navigate autonomously")
    print("  ✓ Detect obstacles")
    print("  ✓ Make smart decisions")
    print("  ✓ Avoid collisions")
    print()
    
    while True:
        print("\nSelect mode:")
        print("  1. Run autonomous mode (30 seconds)")
        print("  2. Run autonomous mode (continuous)")
        print("  3. Test sensors")
        print("  4. Configuration")
        print("  5. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            auto_robot = AutonomousRobot()
            auto_robot.run(duration=30)
        
        elif choice == "2":
            auto_robot = AutonomousRobot()
            auto_robot.run()
        
        elif choice == "3":
            print("\n📡 Testing sensors...")
            print("Press Ctrl+C to stop\n")
            try:
                while True:
                    distance = sensor.distance * 100
                    print(f"Distance: {distance:.2f} cm", end='\r')
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n")
        
        elif choice == "4":
            print(f"\nCurrent Configuration:")
            print(f"  STOP_DISTANCE = {Config.STOP_DISTANCE} cm")
            print(f"  SLOW_DISTANCE = {Config.SLOW_DISTANCE} cm")
            print(f"  SAFE_DISTANCE = {Config.SAFE_DISTANCE} cm")
            print(f"  NORMAL_SPEED = {Config.NORMAL_SPEED}")
            print(f"  DEBUG = {Config.DEBUG}")
            print("\nModify these values in code if needed.")
        
        elif choice == "5":
            break
        
        else:
            print("❌ Invalid choice")
    
    print("\n✅ Program selesai!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        robot.stop()
        status_led.off()
        buzzer.off()
