#!/usr/bin/env python3
"""
Bab 20: Test Complete System - Basic
=====================================
Program sederhana untuk test sistem lengkap

Menguji:
1. Motors
2. Camera
3. Sensors
4. Display
"""

import cv2
import time
from gpiozero import Motor, DistanceSensor, LED
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device

try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*50)
print("Test Complete System - Basic")
print("="*50)

results = {}

print("\n1. Testing Motors...")
try:
    motor_left = Motor(forward=17, backward=27)
    motor_right = Motor(forward=23, backward=24)
    
    motor_left.forward(0.3)
    motor_right.forward(0.3)
    time.sleep(0.5)
    motor_left.stop()
    motor_right.stop()
    
    results['motors'] = "✅ OK"
except Exception as e:
    results['motors'] = f"❌ FAIL: {e}"

print("2. Testing Camera...")
try:
    camera = cv2.VideoCapture(0)
    ret, frame = camera.read()
    if ret:
        results['camera'] = "✅ OK"
    else:
        results['camera'] = "❌ FAIL: No frame"
    camera.release()
except Exception as e:
    results['camera'] = f"❌ FAIL: {e}"

print("3. Testing Ultrasonic...")
try:
    ultrasonic = DistanceSensor(echo=6, trigger=5, max_distance=4)
    distance = ultrasonic.distance * 100
    results['ultrasonic'] = f"✅ OK ({distance:.1f}cm)"
except Exception as e:
    results['ultrasonic'] = f"❌ FAIL: {e}"

print("4. Testing LED...")
try:
    led = LED(12)
    led.on()
    time.sleep(0.2)
    led.off()
    results['led'] = "✅ OK"
except Exception as e:
    results['led'] = f"⚠️  SKIP: {e}"

print("\n" + "="*50)
print("TEST RESULTS:")
print("="*50)

for component, result in results.items():
    print(f"{component.upper():15s} : {result}")

print("="*50)

passed = sum(1 for r in results.values() if '✅' in r)
total = len(results)

print(f"\nPassed: {passed}/{total}")

if passed == total:
    print("✅ All systems operational!")
elif passed >= total * 0.5:
    print("⚠️  Some systems need attention")
else:
    print("❌ Multiple system failures")

print("\n✅ Test selesai!")

"""
PENJELASAN PROGRAM:
==================
Program ini adalah comprehensive system test untuk memverifikasi bahwa semua komponen
hardware robot RTKA berfungsi dengan baik. Ini adalah final check sebelum deploy robot
untuk actual operations.

Tujuan System Testing:
1. Verify hardware connectivity dan functionality
2. Identify failed components early
3. Validate integration antar components
4. Establish baseline performance
5. Document system status

Components yang Ditest:
1. Motors (Actuators):
   - Motor kiri dan kanan untuk differential drive
   - Test: run forward 0.5 detik at 30% speed
   - Verify: no errors, motors respond to commands
   - Critical untuk robot movement

2. Camera (Vision Sensor):
   - USB webcam atau Pi Camera Module
   - Test: open camera dan capture single frame
   - Verify: camera accessible, dapat produce image
   - Critical untuk vision-based applications

3. Ultrasonic Sensor (Distance Sensor):
   - HC-SR04 untuk obstacle detection
   - Test: read distance measurement
   - Verify: sensor responds, returns valid reading
   - Critical untuk autonomous navigation

4. LED (Status Indicator):
   - Optional component untuk status display
   - Test: turn on, delay, turn off
   - Verify: GPIO control works
   - Nice-to-have, not critical (marked as SKIP jika fail)

Test Strategy:
1. Sequential Testing:
   - Test components one by one
   - Independent tests (failure di satu tidak affect others)
   - Continue testing even jika ada failures

2. Error Handling:
   - Try-except untuk each component
   - Capture detailed error messages
   - Distinguish antara FAIL dan SKIP

3. Result Tracking:
   - Dictionary untuk store test results
   - Timestamp dan status untuk each test
   - Summary report at the end

4. Pass/Fail Criteria:
   - All tests pass: "All systems operational"
   - ≥50% pass: "Some systems need attention"
   - <50% pass: "Multiple system failures"

Result Interpretation:

✅ OK:
- Component working perfectly
- Ready untuk operational use
- No action needed

❌ FAIL:
- Component not functioning
- Needs troubleshooting
- Possible issues:
  * Hardware not connected
  * Wrong GPIO pins
  * Insufficient power
  * Driver not installed
  * Permission issues

⚠️ SKIP:
- Component optional atau not available
- System can operate without it
- Nice-to-have feature

Common Failure Causes:

Motors FAIL:
- Wiring issues (loose connections)
- Wrong GPIO pin numbers
- Motor driver not powered
- Insufficient power supply (motors need 5V+, high current)
- Motor driver not enabled

Camera FAIL:
- Camera not connected
- Wrong device index (try 1 instead of 0)
- Camera in use oleh program lain
- Permission issues (user not in video group)
- Pi Camera: interface not enabled di raspi-config

Ultrasonic FAIL:
- Wiring issues (TRIG/ECHO swapped)
- Sensor not powered (VCC, GND)
- GPIO pins incorrect
- Max distance object (sensor return None)

LED FAIL/SKIP:
- GPIO pin already in use
- Wrong pin number
- LED not connected
- Not critical (marked SKIP)

Troubleshooting Steps:
1. Check physical connections:
   - Verify wiring dengan schematic
   - Check for loose wires
   - Multimeter untuk test continuity

2. Verify GPIO pins:
   - Run diagnostic: `gpio readall`
   - Check pin numbering (BCM vs Board)
   - Ensure no conflicts dengan other processes

3. Check permissions:
   - Add user ke gpio/video groups
   - `sudo usermod -a -G gpio,video $USER`

4. Test individual components:
   - Use component-specific test programs
   - Verify dengan simple scripts
   - Check dengan oscilloscope/logic analyzer

5. Power supply:
   - Motors need adequate current (2A+)
   - Voltage stable (~5V untuk motors)
   - Separate power untuk motors (not dari Pi)

System Integration Checklist:
□ All wiring completed dan checked
□ Power supply adequate
□ Software dependencies installed
□ GPIO permissions configured
□ Camera enabled (Pi Camera)
□ All components tested individually
□ Integration test passed
□ Performance benchmark recorded
□ Documentation updated

Next Steps After Testing:

All Pass:
- Proceed to application development
- Calibrate sensors jika needed
- Optimize performance
- Deploy robot

Some Failures:
- Debug failed components
- Check wiring diagram
- Test dengan known-good hardware
- Consult documentation

Multiple Failures:
- Review entire setup
- Check power supply
- Verify software installation
- Consider hardware replacement

Benefits of System Testing:
1. Early Problem Detection:
   - Find issues sebelum complex operations
   - Easier to debug individual components
   - Save time di long run

2. Documentation:
   - Record baseline performance
   - Track component status over time
   - Identify degradation trends

3. Confidence:
   - Know system ready untuk operation
   - Reduce unexpected failures
   - Better reliability

4. Maintenance:
   - Identify components needing replacement
   - Schedule preventive maintenance
   - Track component lifespan

Extension Ideas:
1. Add more tests:
   - Servo motors
   - Line sensors
   - IMU sensor
   - WiFi connectivity
   - Battery voltage

2. Performance metrics:
   - Motor speed accuracy
   - Camera FPS
   - Sensor reading rate
   - Response time

3. Data logging:
   - Save test results to file
   - Timestamp each test
   - Track history over time
   - Generate reports

4. Automated testing:
   - Run tests on boot
   - Scheduled periodic checks
   - Alert on failures
   - Remote monitoring

5. Visual dashboard:
   - Web interface untuk status
   - Real-time component monitoring
   - Historical data graphs
   - Remote diagnostics

This comprehensive testing approach ensures robot reliability dan readiness untuk
actual deployment di real-world applications.
"""
