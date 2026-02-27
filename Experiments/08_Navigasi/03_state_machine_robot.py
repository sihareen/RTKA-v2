#!/usr/bin/env python3
"""
Bab 8.3: State Machine Dasar Robot
===================================
State Machine untuk mengatur behavior robot yang kompleks

Konsep State Machine:
- State = kondisi/keadaan robot saat ini
- Transition = perpindahan dari satu state ke state lain
- Event = trigger yang menyebabkan transition

Contoh States untuk Robot:
1. IDLE = Berhenti, menunggu
2. MOVING_FORWARD = Bergerak maju
3. AVOIDING_OBSTACLE = Menghindari halangan
4. TURNING = Berbelok
5. REVERSING = Mundur

State Diagram:
              ┌──────────┐
    START ───>│   IDLE   │
              └────┬─────┘
                   │ start_cmd
                   ▼
         ┌────────────────┐
         │ MOVING_FORWARD │
         └────┬───────────┘
              │ obstacle_detected
              ▼
      ┌───────────────┐
      │   REVERSING   │
      └───────┬───────┘
              │ reversed_enough
              ▼
       ┌─────────┐
       │ TURNING │
       └────┬────┘
            │ turn_complete
            └──> back to MOVING_FORWARD

Hardware:
- 4WD Robot
- Ultrasonic Sensor
- LED indicators (optional)
"""

from gpiozero import Motor, DistanceSensor, LED
from time import sleep, time
from enum import Enum

# Setup Hardware
motor_fl = Motor(forward=17, backward=27)
motor_rl = Motor(forward=22, backward=23)
motor_fr = Motor(forward=10, backward=25)
motor_rr = Motor(forward=16, backward=9)

sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0)

# LED indicators (optional)
try:
    led_status = LED(7)  # Status LED
except:
    led_status = None

# Define States
class RobotState(Enum):
    IDLE = "idle"
    MOVING_FORWARD = "moving_forward"
    REVERSING = "reversing"
    TURNING = "turning"
    AVOIDING = "avoiding"
    STOPPED = "stopped"

print("="*70)
print("State Machine - Robot Behavior Control")
print("="*70)

class RobotStateMachine:
    """State Machine untuk kontrol robot"""
    
    def __init__(self):
        self.current_state = RobotState.IDLE
        self.previous_state = None
        self.state_start_time = time()
        
        # Parameters
        self.safe_distance = 30  # cm
        self.speed = 0.4
        
        # Counters
        self.transitions = 0
        self.obstacle_count = 0
    
    def get_distance(self):
        """Baca jarak dari sensor"""
        try:
            return sensor.distance * 100
        except:
            return 999  # Return large value if error
    
    def move_forward(self):
        """Gerak maju"""
        motor_fl.forward(self.speed)
        motor_rl.forward(self.speed)
        motor_fr.forward(self.speed)
        motor_rr.forward(self.speed)
    
    def move_backward(self):
        """Gerak mundur"""
        motor_fl.backward(self.speed)
        motor_rl.backward(self.speed)
        motor_fr.backward(self.speed)
        motor_rr.backward(self.speed)
    
    def turn_right(self):
        """Belok kanan"""
        motor_fl.forward(self.speed)
        motor_rl.forward(self.speed)
        motor_fr.backward(self.speed)
        motor_rr.backward(self.speed)
    
    def stop_motors(self):
        """Stop semua motor"""
        motor_fl.stop()
        motor_rl.stop()
        motor_fr.stop()
        motor_rr.stop()
    
    def change_state(self, new_state):
        """Ubah state dengan logging"""
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_start_time = time()
            self.transitions += 1
            
            print(f"\n[STATE] {self.previous_state.value} → {new_state.value}")
            
            if led_status:
                led_status.on() if new_state != RobotState.IDLE else led_status.off()
    
    def time_in_state(self):
        """Berapa lama di state saat ini"""
        return time() - self.state_start_time
    
    def state_idle(self):
        """State: IDLE"""
        self.stop_motors()
        
        # Transition to MOVING_FORWARD after 1 second
        if self.time_in_state() > 1.0:
            self.change_state(RobotState.MOVING_FORWARD)
    
    def state_moving_forward(self):
        """State: MOVING_FORWARD"""
        distance = self.get_distance()
        
        print(f"  Distance: {distance:5.1f} cm", end="\r")
        
        # Check obstacle
        if distance < self.safe_distance:
            self.obstacle_count += 1
            self.change_state(RobotState.AVOIDING)
        else:
            self.move_forward()
    
    def state_reversing(self):
        """State: REVERSING"""
        self.move_backward()
        
        # Reverse for 0.8 seconds
        if self.time_in_state() > 0.8:
            self.change_state(RobotState.TURNING)
    
    def state_turning(self):
        """State: TURNING"""
        self.turn_right()
        
        # Turn for 0.7 seconds
        if self.time_in_state() > 0.7:
            self.change_state(RobotState.MOVING_FORWARD)
    
    def state_avoiding(self):
        """State: AVOIDING (composite state)"""
        # Stop briefly
        self.stop_motors()
        
        if self.time_in_state() > 0.3:
            self.change_state(RobotState.REVERSING)
    
    def state_stopped(self):
        """State: STOPPED"""
        self.stop_motors()
    
    def update(self):
        """Update state machine (dipanggil setiap loop)"""
        # Dispatch ke handler sesuai state
        if self.current_state == RobotState.IDLE:
            self.state_idle()
        elif self.current_state == RobotState.MOVING_FORWARD:
            self.state_moving_forward()
        elif self.current_state == RobotState.REVERSING:
            self.state_reversing()
        elif self.current_state == RobotState.TURNING:
            self.state_turning()
        elif self.current_state == RobotState.AVOIDING:
            self.state_avoiding()
        elif self.current_state == RobotState.STOPPED:
            self.state_stopped()
    
    def print_stats(self):
        """Print statistik"""
        print(f"\n{'='*70}")
        print("State Machine Statistics:")
        print(f"  Total Transitions: {self.transitions}")
        print(f"  Obstacles Avoided: {self.obstacle_count}")
        print(f"  Final State: {self.current_state.value}")
        print(f"{'='*70}")

def run_state_machine(duration=30):
    """Jalankan state machine untuk durasi tertentu"""
    robot = RobotStateMachine()
    
    print(f"\nRunning state machine for {duration} seconds...")
    print("Tekan Ctrl+C untuk stop\n")
    
    start_time = time()
    
    try:
        while (time() - start_time) < duration:
            robot.update()
            sleep(0.1)  # 10 Hz update rate
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    finally:
        robot.change_state(RobotState.STOPPED)
        robot.print_stats()
        robot.stop_motors()

def demonstrate_states():
    """Demonstrasi manual setiap state"""
    robot = RobotStateMachine()
    
    states_demo = [
        (RobotState.IDLE, 2, "Robot idle"),
        (RobotState.MOVING_FORWARD, 3, "Moving forward"),
        (RobotState.REVERSING, 1, "Reversing"),
        (RobotState.TURNING, 1, "Turning right"),
        (RobotState.STOPPED, 1, "Stopped"),
    ]
    
    print("\nDemonstrasi Manual States:")
    print("-" * 70)
    
    for state, duration, description in states_demo:
        print(f"\n{description}...")
        robot.change_state(state)
        
        for i in range(int(duration * 10)):
            robot.update()
            sleep(0.1)
    
    robot.stop_motors()
    print("\n✅ Demonstrasi selesai")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

try:
    print("\n📖 State Machine Concept:")
    print("  - Mengorganisir behavior robot ke dalam states")
    print("  - Setiap state punya action dan transition rules")
    print("  - Lebih mudah di-maintain dan di-debug")
    print("  - Scalable untuk behavior kompleks")
    print()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Run State Machine (30 detik)")
        print("  2. Run State Machine (60 detik)")
        print("  3. Manual State Demonstration")
        print("  4. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            input("\n⚠️  Robot akan bergerak! Tekan ENTER untuk mulai...")
            run_state_machine(duration=30)
        elif choice == "2":
            input("\n⚠️  Robot akan bergerak! Tekan ENTER untuk mulai...")
            run_state_machine(duration=60)
        elif choice == "3":
            input("\nTekan ENTER untuk demonstrasi...")
            demonstrate_states()
        elif choice == "4":
            break
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")
    print("\n💡 Advanced Topics:")
    print("  - Hierarchical State Machines")
    print("  - Event-driven transitions")
    print("  - State persistence (save/load)")
    print("  - Multiple concurrent state machines")

except KeyboardInterrupt:
    print("\n\n🛑 Emergency Stop!")

finally:
    motor_fl.stop()
    motor_rl.stop()
    motor_fr.stop()
    motor_rr.stop()
    if led_status:
        led_status.off()
    print("\nAll motors stopped & GPIO released")
