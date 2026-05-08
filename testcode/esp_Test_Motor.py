import uasyncio as asyncio
from machine import Pin, PWM
import sys, select
import time

# === Motor pin configuration ===
# Motor 1 pins
MOTOR1_DIR = Pin(26, Pin.OUT)  
MOTOR1_EN = Pin(25, Pin.OUT)
MOTOR1_CLK = Pin(27, Pin.OUT)

# Motor 2 pins
MOTOR2_DIR = Pin(4, Pin.OUT)
MOTOR2_EN = Pin(5, Pin.OUT)
MOTOR2_CLK = Pin(15, Pin.OUT)

# Motor enable state (0: enabled, 1: disabled)
ENABLE_ACTIVE = 0

# Stepper motor configuration
STEP_ANGLE = 1.8  # Step angle (degrees)
STEPS_PER_REV = int(360 / STEP_ANGLE)  # Steps per revolution (200 steps)
# MICROSTEP = 8  # 1/8 microstepping
MICROSTEP = 1  # Motor driver doesn't work with configured microstepping
ACTUAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEP

# PWM objects
pwm1 = None
pwm2 = None

# Motor state class
class MotorState:
    def __init__(self):
        self.steps_per_second = 1  # Initial value: 1 step per second
        self.direction = 1  # 1: clockwise, 0: counterclockwise
        self.running = False  # Motor operation state
        self.target_steps = 1  # Target step count
        
# Create motor state objects
motor1 = MotorState()
motor2 = MotorState()
motor2.direction = 0  # Initialize motor2 in opposite direction

# Steps to frequency conversion function
def steps_to_freq(steps_per_second):
    if steps_per_second <= 0:
        return 0
    return steps_per_second

# Motor initialization
def init_motors():
    global pwm1, pwm2
    
    # Enable motors
    MOTOR1_EN.value(ENABLE_ACTIVE)
    MOTOR2_EN.value(ENABLE_ACTIVE)
    
    # Set direction
    MOTOR1_DIR.value(motor1.direction)
    MOTOR2_DIR.value(motor2.direction)
    
    # Create PWM objects (initial frequency: 1 step per second)
    motor1.running = True
    motor2.running = True
    
    pwm1 = PWM(MOTOR1_CLK, freq=steps_to_freq(motor1.steps_per_second), duty=512)
    pwm2 = PWM(MOTOR2_CLK, freq=steps_to_freq(motor2.steps_per_second), duty=512)
    
    print(f"Motor1 initialized: {motor1.steps_per_second} steps/sec, direction: {'clockwise' if motor1.direction else 'counterclockwise'}")
    print(f"Motor2 initialized: {motor2.steps_per_second} steps/sec, direction: {'clockwise' if motor2.direction else 'counterclockwise'}")

# Update motor speed
def update_motor_speed(motor, pwm):
    if motor.running and motor.steps_per_second > 0:
        # Set frequency
        freq = steps_to_freq(motor.steps_per_second)
        pwm.freq(freq)
        pwm.duty(512)  # 50% duty cycle
    else:
        # Stop state
        pwm.duty(0)

async def accelerate_motor(motor, pwm, target_steps, max_time_ms=2000):
    """Log scale acceleration to reach target speed within maximum 2 seconds"""
    start_steps = max(1, motor.steps_per_second)
    steps_diff = target_steps - start_steps
    
    if steps_diff == 0:
        return
        
    # Calculate acceleration/deceleration steps (limited to maximum 100 steps)
    num_steps = min(100, abs(steps_diff))
    delay_ms = max_time_ms // num_steps
    
    if steps_diff > 0:  # Acceleration
        for i in range(num_steps):
            # Log scale increase (slow at first, fast later)
            progress = (i + 1) / num_steps
            current = start_steps + int(steps_diff * (progress ** 2))
            
            motor.steps_per_second = current
            update_motor_speed(motor, pwm)
            await asyncio.sleep_ms(delay_ms)
    else:  # Deceleration
        for i in range(num_steps):
            # Exponential scale decrease (fast at first, slow later)
            progress = (i + 1) / num_steps
            current = start_steps + int(steps_diff * progress)
            
            motor.steps_per_second = current
            update_motor_speed(motor, pwm)
            await asyncio.sleep_ms(delay_ms)
    
    # Set final target step count
    motor.steps_per_second = target_steps
    update_motor_speed(motor, pwm)

# Stop motor
def stop_motor(motor, pwm):
    motor.running = False
    motor.steps_per_second = 0
    update_motor_speed(motor, pwm)

# Keyboard input task
async def keyboard_input_task():
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().strip()
            try:
                # Motor1 input: "1 number" format
                if line.startswith("1 "):
                    steps = int(line.split()[1])
                    motor1.target_steps = steps
                    if steps == 0:
                        stop_motor(motor1, pwm1)
                        print(f"Motor1 stopped")
                    else:
                        asyncio.create_task(accelerate_motor(motor1, pwm1, steps))
                        print(f"Motor1 speed changed: {steps} steps/sec")
                
                # Motor2 input: "2 number" format
                elif line.startswith("2 "):
                    steps = int(line.split()[1])
                    motor2.target_steps = steps
                    if steps == 0:
                        stop_motor(motor2, pwm2)
                        print(f"Motor2 stopped")
                    else:
                        asyncio.create_task(accelerate_motor(motor2, pwm2, steps))
                        print(f"Motor2 speed changed: {steps} steps/sec")
                
                # Both motors input: "0 number" format
                elif line.startswith("0 "):
                    steps = int(line.split()[1])
                    motor1.target_steps = steps
                    motor2.target_steps = steps
                    if steps == 0:
                        stop_motor(motor1, pwm1)
                        stop_motor(motor2, pwm2)
                        print("All motors stopped")
                    else:
                        asyncio.create_task(accelerate_motor(motor1, pwm1, steps))
                        asyncio.create_task(accelerate_motor(motor2, pwm2, steps))
                        print(f"All motors speed changed: {steps} steps/sec")
                
                # Direction change: "d1" or "d2" or "d0"(both)
                elif line == "d1":
                    motor1.direction = not motor1.direction
                    MOTOR1_DIR.value(motor1.direction)
                    print(f"Motor1 direction changed: {'clockwise' if motor1.direction else 'counterclockwise'}")
                elif line == "d2":
                    motor2.direction = not motor2.direction
                    MOTOR2_DIR.value(motor2.direction)
                    print(f"Motor2 direction changed: {'clockwise' if motor2.direction else 'counterclockwise'}")
                elif line == "d0":
                    motor1.direction = not motor1.direction
                    motor2.direction = not motor2.direction
                    MOTOR1_DIR.value(motor1.direction)
                    MOTOR2_DIR.value(motor2.direction)
                    print(f"All motors direction changed: Motor1={'clockwise' if motor1.direction else 'counterclockwise'}, Motor2={'clockwise' if motor2.direction else 'counterclockwise'}")
                
                # Help
                elif line == "help":
                    print("Command help:")
                    print("1 n : Set motor1 speed to n steps per second")
                    print("2 n : Set motor2 speed to n steps per second")
                    print("0 n : Set both motors speed to n steps per second")
                    print("d1  : Toggle motor1 direction")
                    print("d2  : Toggle motor2 direction")
                    print("d0  : Toggle both motors direction")
                    print("help: Show help")
            except Exception as e:
                print(f"Input processing error: {e}")
                print("Correct format: '1 number' or '2 number' or 'd1' etc.")
        
        await asyncio.sleep_ms(100)

# Status report task
async def status_report_task():
    while True:
        print(f"Motor1: {'running' if motor1.running else 'stopped'}, {motor1.steps_per_second} steps/sec, direction: {'clockwise' if motor1.direction else 'counterclockwise'}")
        print(f"Motor2: {'running' if motor2.running else 'stopped'}, {motor2.steps_per_second} steps/sec, direction: {'clockwise' if motor2.direction else 'counterclockwise'}")
        await asyncio.sleep(5)  # Status output every 5 seconds

# Main function
async def main():
    # Initialize motors
    init_motors()
    
    # Create tasks
    input_task = asyncio.create_task(keyboard_input_task())
    status_task = asyncio.create_task(status_report_task())
    
    print("Stepper motor control program started")
    print("Command format:")
    print("1 n : Set motor1 speed to n steps per second")
    print("2 n : Set motor2 speed to n steps per second")
    print("0 n : Set both motors speed to n steps per second")
    print("d1  : Toggle motor1 direction")
    print("d2  : Toggle motor2 direction")
    print("d0  : Toggle both motors direction")
    print("help: Show help")
    
    try:
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Cleanup
        if pwm1:
            pwm1.deinit()
        if pwm2:
            pwm2.deinit()
        # Disable motors
        MOTOR1_EN.value(not ENABLE_ACTIVE)
        MOTOR2_EN.value(not ENABLE_ACTIVE)

# Execute
try:
    asyncio.run(main())
except KeyboardInterrupt:
    # Cleanup
    if 'pwm1' in globals() and pwm1:
        pwm1.deinit()
    if 'pwm2' in globals() and pwm2:
        pwm2.deinit()
    # Disable motors
    MOTOR1_EN.value(not ENABLE_ACTIVE)
    MOTOR2_EN.value(not ENABLE_ACTIVE)
    print("Program terminated.")