import uasyncio as asyncio
from machine import Pin, PWM, I2C
import sys, select
import time
import math

# === MPU6050 sensor configuration ===
MPU6050_ADDR = 0x68  # MPU6050 device address
ACCEL_XOUT_H = 0x3B  # Accelerometer X-axis high byte register address
GYRO_XOUT_H = 0x43   # Gyroscope X-axis high byte register address
PWR_MGMT_1 = 0x6B    # Power management register 1

# Complementary filter settings
COMPLEMENTARY_WEIGHT = 0.98  # Gyroscope data weight
SAMPLING_TIME = 0.1   # Sampling time (100ms = 0.1 seconds)

# Global variables to store sensor data
current_angle_x = 0
current_angle_y = 0

# Sensor calibration global variables
gyro_offset_x = 0
gyro_offset_y = 0
gyro_offset_z = 0
accel_offset_x = 0
accel_offset_y = 0
accel_offset_z = 0

# === Motor configuration ===
STEP_ANGLE = 1.8  # Step angle (degrees)
STEPS_PER_REV = int(360 / STEP_ANGLE)  # Steps per revolution (200 steps)
GEAR_RATIO = 2  # Gear ratio 2:1

# Microstepping settings
# Example: 1=full step, 2=half step, 4=1/4 step, 8=1/8 step, 16=1/16 step
MICROSTEP = 8
ACTUAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEP

# RPM to frequency (Hz) conversion
def rpm_to_freq(rpm):
    if rpm <= 0:
        return 0
    # RPM -> steps per second (Hz), considering microstepping
    return (rpm * ACTUAL_STEPS_PER_REV) / 60

# Speed limits - directly set in RPM
MIN_RPM = 2.0  # Minimum RPM (stable minimum speed)
MAX_RPM = 196.0  # Maximum RPM (stable maximum speed). (1.11m/s * 60 / 0.678m) * 2 = ca. 196.4 RPM
BASE_RPM = 30.0  # Initial recommended RPM

# PWM limits
MIN_PWM_FREQ = 50     # Minimum PWM frequency (Hz) - ensures low speed stability
MAX_PWM_FREQ = 25000  # Maximum PWM frequency (Hz)

# Speed adjustment units (1 RPM, 10 RPM)
RPM_STEP_SMALL = 1.0  # 1 RPM unit
RPM_STEP_LARGE = 10.0  # 10 RPM unit

# === Motor 1 pin configuration ===
MOTOR1_DIR = Pin(26, Pin.OUT)
MOTOR1_EN  = Pin(25, Pin.OUT)
MOTOR1_CLK = Pin(27, Pin.OUT)

# === Motor 2 pin configuration ===
MOTOR2_DIR = Pin(4, Pin.OUT)
MOTOR2_EN  = Pin(5, Pin.OUT)
MOTOR2_CLK = Pin(15, Pin.OUT)

# === Motor driver dependent EN pin activation state ===
ENABLE_ACTIVE = 0  # 0 for active (A4988, DRV8825, etc.), 1 for inactive

# PWM object creation
pwm1 = None
pwm2 = None

# Motor state initialization
class MotorState:
    def __init__(self):
        self.rpm = BASE_RPM
        self.direction = 1  # 1: clockwise, 0: counterclockwise
        self.running = True  # True: running, False: stopped
        self.freq = rpm_to_freq(BASE_RPM)

# Create motor state objects
motor1 = MotorState()
motor2 = MotorState()

# === MPU6050 sensor initialization and control functions ===
def init_mpu6050(i2c):
    """Initialize MPU6050 sensor"""
    # Device check
    try:
        devices = i2c.scan()
        if MPU6050_ADDR not in devices:
            print(f"MPU6050 sensor not found. Found devices: {devices}")
            return False
            
        # Sensor initialization - wake up from sleep mode
        i2c.writeto_mem(MPU6050_ADDR, PWR_MGMT_1, bytes([0]))
        time.sleep_ms(100)  # Wait for initialization
        return True
    except Exception as e:
        print(f"MPU6050 initialization error: {e}")
        return False

def calibrate_mpu6050(i2c, samples=100):
    """MPU6050 sensor calibration
    
    Args:
        i2c: I2C object
        samples: Number of samples to use for calibration
    
    Returns:
        bool: Calibration success status
    """
    global gyro_offset_x, gyro_offset_y, gyro_offset_z
    global accel_offset_x, accel_offset_y, accel_offset_z
    
    print(f"MPU6050 calibration starting ({samples} samples)...")
    print("Place sensor on flat surface and do not move...")
    time.sleep(2)  # Time for user to stabilize sensor
    
    try:
        # Calibration initialization
        gyro_sum_x = gyro_sum_y = gyro_sum_z = 0
        accel_sum_x = accel_sum_y = accel_sum_z = 0
        
        # Collect multiple samples
        for i in range(samples):
            # Read raw data
            accel_x = read_raw_data(i2c, ACCEL_XOUT_H)
            accel_y = read_raw_data(i2c, ACCEL_XOUT_H + 2)
            accel_z = read_raw_data(i2c, ACCEL_XOUT_H + 4)
            
            gyro_x = read_raw_data(i2c, GYRO_XOUT_H)
            gyro_y = read_raw_data(i2c, GYRO_XOUT_H + 2)
            gyro_z = read_raw_data(i2c, GYRO_XOUT_H + 4)
            
            # Accumulate sums
            gyro_sum_x += gyro_x
            gyro_sum_y += gyro_y
            gyro_sum_z += gyro_z
            
            accel_sum_x += accel_x
            accel_sum_y += accel_y
            accel_sum_z += accel_z
            
            # Show progress (every 10 samples)
            if i % 10 == 0:
                print(f"Calibration in progress... {i}/{samples}")
                
            time.sleep_ms(20)  # Slight delay between samples
        
        # Calculate average values
        gyro_offset_x = gyro_sum_x / samples
        gyro_offset_y = gyro_sum_y / samples
        gyro_offset_z = gyro_sum_z / samples
        
        accel_offset_x = accel_sum_x / samples
        accel_offset_y = accel_sum_y / samples
        # Z-axis acceleration includes gravity (1g), so handle differently
        # 16384 is the value corresponding to 1g in ±2g range
        accel_offset_z = accel_sum_z / samples - 16384
        
        print("=== Calibration Complete ===")
        print("Calibration result values:")
        print(f"Gyro offsets - X: {gyro_offset_x:.2f}, Y: {gyro_offset_y:.2f}, Z: {gyro_offset_z:.2f}")
        print(f"Accel offsets - X: {accel_offset_x:.2f}, Y: {accel_offset_y:.2f}, Z: {accel_offset_z:.2f}")
        print("---------------------------")
        print("Copy the values below to use in your code:")
        print(f"gyro_offset_x = {gyro_offset_x:.2f}")
        print(f"gyro_offset_y = {gyro_offset_y:.2f}")
        print(f"gyro_offset_z = {gyro_offset_z:.2f}")
        print(f"accel_offset_x = {accel_offset_x:.2f}")
        print(f"accel_offset_y = {accel_offset_y:.2f}")
        print(f"accel_offset_z = {accel_offset_z:.2f}")
        print("---------------------------")
        
        return True
        
    except Exception as e:
        print(f"Calibration error: {e}")
        return False

def read_raw_data(i2c, addr):
    """Read 2-byte raw data from specific register"""
    high = i2c.readfrom_mem(MPU6050_ADDR, addr, 1)[0]
    low = i2c.readfrom_mem(MPU6050_ADDR, addr + 1, 1)[0]
    value = (high << 8) | low
    
    # Two's complement processing (16-bit negative number handling)
    if value > 32767:
        value -= 65536
    return value

def read_mpu6050(i2c):
    """Read acceleration and gyro data from MPU6050 (with calibration applied)"""
    try:
        # Read accelerometer values (measured in ±2g range)
        accel_x = read_raw_data(i2c, ACCEL_XOUT_H)
        accel_y = read_raw_data(i2c, ACCEL_XOUT_H + 2)
        accel_z = read_raw_data(i2c, ACCEL_XOUT_H + 4)
        
        # Read gyroscope values (measured in ±250°/s range)
        gyro_x = read_raw_data(i2c, GYRO_XOUT_H)
        gyro_y = read_raw_data(i2c, GYRO_XOUT_H + 2)
        gyro_z = read_raw_data(i2c, GYRO_XOUT_H + 4)
        
        # Apply calibration offsets
        accel_x -= accel_offset_x
        accel_y -= accel_offset_y
        accel_z -= accel_offset_z
        
        gyro_x -= gyro_offset_x
        gyro_y -= gyro_offset_y
        gyro_z -= gyro_offset_z
        
        # Convert acceleration values (±2g range with 16384 LSB/g)
        ax = accel_x / 16384.0  # g units
        ay = accel_y / 16384.0
        az = accel_z / 16384.0
        
        # Convert gyro values (±250°/s range with 131 LSB/°/s)
        gx = gyro_x / 131.0  # degrees/second units
        gy = gyro_y / 131.0
        gz = gyro_z / 131.0
        
        return ax, ay, az, gx, gy, gz
    except Exception as e:
        print(f"MPU6050 data reading error: {e}")
        return 0, 0, 0, 0, 0, 0

def calculate_angles(ax, ay, az, gx, gy, gz, prev_angle_x, prev_angle_y, dt):
    """Calculate angles using complementary filter"""
    # Calculate angles from accelerometer (convert from radians to degrees)
    accel_angle_x = math.atan2(ay, az) * 180 / math.pi
    accel_angle_y = math.atan2(-ax, az) * 180 / math.pi
    
    # Calculate angle changes from gyro measurements (degrees/second * seconds = degrees)
    gyro_angle_x = prev_angle_x + gx * dt
    gyro_angle_y = prev_angle_y + gy * dt
    
    # Apply complementary filter (high weight for gyro, low weight for accelerometer)
    angle_x = COMPLEMENTARY_WEIGHT * gyro_angle_x + (1 - COMPLEMENTARY_WEIGHT) * accel_angle_x
    angle_y = COMPLEMENTARY_WEIGHT * gyro_angle_y + (1 - COMPLEMENTARY_WEIGHT) * accel_angle_y
    
    return angle_x, angle_y

# Limit RPM to safe frequency range
def safe_freq(rpm):
    freq = rpm_to_freq(rpm)
    if freq < MIN_PWM_FREQ and freq > 0:
        freq = MIN_PWM_FREQ
    elif freq > MAX_PWM_FREQ:
        freq = MAX_PWM_FREQ
    return int(freq)

# Motor PWM initialization
def init_pwm():
    global pwm1, pwm2
    
    # Enable motors
    MOTOR1_EN.value(ENABLE_ACTIVE)
    MOTOR2_EN.value(ENABLE_ACTIVE)
    
    # Set directions
    MOTOR1_DIR.value(motor1.direction)
    MOTOR2_DIR.value(motor2.direction)
    
    # PWM object creation (initial frequency setting)
    motor1.freq = safe_freq(motor1.rpm)
    motor2.freq = safe_freq(motor2.rpm)
    
    # Create PWM and set duty cycle (50%)
    pwm1 = PWM(MOTOR1_CLK, freq=motor1.freq, duty=512)
    pwm2 = PWM(MOTOR2_CLK, freq=motor2.freq, duty=512)
    
    # Disable PWM if motor is in stop state
    if not motor1.running or motor1.rpm <= 0:
        pwm1.duty(0)
    
    if not motor2.running or motor2.rpm <= 0:
        pwm2.duty(0)
    
    print(f"Motor1: {motor1.rpm:.1f} RPM, direction: {'clockwise' if motor1.direction else 'counterclockwise'}, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    print(f"Motor2: {motor2.rpm:.1f} RPM, direction: {'clockwise' if motor2.direction else 'counterclockwise'}")

# Update motor speed
def update_motor_speed(motor, pwm):
    if motor.running and motor.rpm > 0:
        # If RPM is below minimum and above 0, set to minimum
        if motor.rpm < MIN_RPM and motor.rpm > 0:
            motor.rpm = MIN_RPM
        
        # Calculate frequency and check safe range
        motor.freq = safe_freq(motor.rpm)
        
        # Set PWM frequency and duty
        pwm.freq(motor.freq)
        pwm.duty(512)  # 50% duty cycle
    else:
        # Immediately disable PWM when stopped
        pwm.duty(0)

# Function to stop both wheels
def stop_all_motors():
    motor1.running = False
    motor2.running = False
    motor1.rpm = 0
    motor2.rpm = 0
    update_motor_speed(motor1, pwm1)
    update_motor_speed(motor2, pwm2)
    print(f"All motors stopped. Tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")

# Function to reverse rotation direction of both wheels
def reverse_all_directions():
    # Temporarily stop motors
    temp_running1 = motor1.running
    temp_rpm1 = motor1.rpm
    temp_running2 = motor2.running
    temp_rpm2 = motor2.rpm
    
    motor1.running = False
    motor2.running = False
    motor1.rpm = 0
    motor2.rpm = 0
    update_motor_speed(motor1, pwm1)
    update_motor_speed(motor2, pwm2)
    
    # Slight delay before direction change
    time.sleep_ms(50)
    
    # Change directions
    motor1.direction = not motor1.direction
    motor2.direction = not motor2.direction
    MOTOR1_DIR.value(motor1.direction)
    MOTOR2_DIR.value(motor2.direction)
    
    # Restore original state
    motor1.running = temp_running1
    motor1.rpm = temp_rpm1
    motor2.running = temp_running2
    motor2.rpm = temp_rpm2
    update_motor_speed(motor1, pwm1)
    update_motor_speed(motor2, pwm2)
    
    print(f"All motor directions reversed. Tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    print(f"Motor1 direction: {'clockwise' if motor1.direction else 'counterclockwise'}, Motor2 direction: {'clockwise' if motor2.direction else 'counterclockwise'}")

# === MPU6050 sensor task ===
async def mpu6050_task():
    """MPU6050 sensor measurement async task"""
    global current_angle_x, current_angle_y
    
    print("Initializing MPU6050 sensor...")
    # I2C initialization (SDA=21, SCL=22)
    i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
    
    # Sensor initialization
    if not init_mpu6050(i2c):
        print("MPU6050 sensor initialization failed")
        return
    
    print("MPU6050 sensor initialization complete, measurement started")
    
    # Calibration function (commented out)
    # Uncomment below lines if needed
    """
    print("Starting sensor calibration...")
    if calibrate_mpu6050(i2c):
        print("Calibration successfully completed.")
    else:
        print("Calibration failed, continuing with default values.")
    
    # Check offset values after calibration
    print("Currently used offset values:")
    print(f"Gyro offsets - X: {gyro_offset_x:.2f}, Y: {gyro_offset_y:.2f}, Z: {gyro_offset_z:.2f}")
    print(f"Accel offsets - X: {accel_offset_x:.2f}, Y: {accel_offset_y:.2f}, Z: {accel_offset_z:.2f}")
    """
    
    # Display currently used offset values
    print("Currently used offset values:")
    print(f"Gyro offsets - X: {gyro_offset_x:.2f}, Y: {gyro_offset_y:.2f}, Z: {gyro_offset_z:.2f}")
    print(f"Accel offsets - X: {accel_offset_x:.2f}, Y: {accel_offset_y:.2f}, Z: {accel_offset_z:.2f}")
    
    # Initial angle values (0)
    angle_x = 0
    angle_y = 0
    
    # Store previous time
    last_time = time.time()
    
    while True:
        try:
            # Calculate current time and elapsed time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Read sensor data (with calibration values applied)
            ax, ay, az, gx, gy, gz = read_mpu6050(i2c)
            
            # Calculate angles with complementary filter
            angle_x, angle_y = calculate_angles(ax, ay, az, gx, gy, gz, angle_x, angle_y, dt)
            
            # Update global variables
            current_angle_x = angle_x
            current_angle_y = angle_y
            
        except Exception as e:
            print(f"Sensor task error: {e}")
        
        # Measure every 0.1 seconds (100ms, 10Hz)
        await asyncio.sleep(SAMPLING_TIME)

# === USB (PC) key input handling ===
async def usb_input_task():
    """Receive key input from USB (PC)"""
    while True:
        try:
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                try:
                    key = sys.stdin.read(1).upper()
                    if key in "QAWSEDRFXCP":  # Added P key
                        handle_key_input(key)
                except:
                    pass
        except Exception as e:
            print(f"USB input error: {e}")
        await asyncio.sleep(0.1)

def handle_key_input(key):
    """Common key input handling"""
    # Store previous speeds
    old_rpm1 = motor1.rpm
    old_rpm2 = motor2.rpm
    
    # Sensor calibration command
    if key == 'P':  # Start calibration with P key
        print("\n===== MPU6050 Sensor Calibration Start =====")
        print("Temporarily stopping motors for calibration...")
        
        # Save motor states
        temp_motor1_running = motor1.running
        temp_motor1_rpm = motor1.rpm
        temp_motor2_running = motor2.running
        temp_motor2_rpm = motor2.rpm
        
        # Stop motors
        motor1.running = False
        motor2.running = False
        update_motor_speed(motor1, pwm1)
        update_motor_speed(motor2, pwm2)
        
        # Execute sensor calibration
        i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
        calibration_success = calibrate_mpu6050(i2c)
        
        # Restore motor states
        print("Restoring motor states...")
        motor1.running = temp_motor1_running
        motor1.rpm = temp_motor1_rpm
        motor2.running = temp_motor2_running
        motor2.rpm = temp_motor2_rpm
        update_motor_speed(motor1, pwm1)
        update_motor_speed(motor2, pwm2)
        
        if calibration_success:
            print("Calibration successfully completed.")
        else:
            print("Calibration failed, continuing with previous values.")
            
        print(f"Motor states restored:")
        print(f"Motor1: {'running' if motor1.running else 'stopped'}, {motor1.rpm:.1f} RPM, direction: {'clockwise' if motor1.direction else 'counterclockwise'}")
        print(f"Motor2: {'running' if motor2.running else 'stopped'}, {motor2.rpm:.1f} RPM, direction: {'clockwise' if motor2.direction else 'counterclockwise'}")
        print(f"Current tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
        
        return
    
    # Motor 1 control
    if key == 'Q':  # Motor 1 speed increase by 10 RPM
        motor1.rpm = min(motor1.rpm + RPM_STEP_LARGE, MAX_RPM)
        motor1.running = True
        print(f"Motor1 speed increased (10 RPM): {old_rpm1:.1f} -> {motor1.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    elif key == 'A':  # Motor 1 speed decrease by 10 RPM
        motor1.rpm = max(motor1.rpm - RPM_STEP_LARGE, 0)
        print(f"Motor1 speed decreased (10 RPM): {old_rpm1:.1f} -> {motor1.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
        if motor1.rpm == 0:
            motor1.running = False
        elif motor1.rpm < MIN_RPM:
            # Stop motor if below minimum speed
            motor1.running = False
            motor1.rpm = 0
            print(f"Motor1 below minimum speed: stopped, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    elif key == 'E':  # Motor 1 speed increase by 1 RPM
        motor1.rpm = min(motor1.rpm + RPM_STEP_SMALL, MAX_RPM)
        motor1.running = True
        print(f"Motor1 speed increased (1 RPM): {old_rpm1:.1f} -> {motor1.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    elif key == 'D':  # Motor 1 speed decrease by 1 RPM
        motor1.rpm = max(motor1.rpm - RPM_STEP_SMALL, 0)
        print(f"Motor1 speed decreased (1 RPM): {old_rpm1:.1f} -> {motor1.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
        if motor1.rpm == 0:
            motor1.running = False
        elif motor1.rpm < MIN_RPM:
            # Stop motor if below minimum speed
            motor1.running = False
            motor1.rpm = 0
            print(f"Motor1 below minimum speed: stopped, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    
    # Motor 2 control
    elif key == 'W':  # Motor 2 speed increase by 10 RPM
        motor2.rpm = min(motor2.rpm + RPM_STEP_LARGE, MAX_RPM)
        motor2.running = True
        print(f"Motor2 speed increased (10 RPM): {old_rpm2:.1f} -> {motor2.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    elif key == 'S':  # Motor 2 speed decrease by 10 RPM
        motor2.rpm = max(motor2.rpm - RPM_STEP_LARGE, 0)
        print(f"Motor2 speed decreased (10 RPM): {old_rpm2:.1f} -> {motor2.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
        if motor2.rpm == 0:
            motor2.running = False
        elif motor2.rpm < MIN_RPM:
            # Stop motor if below minimum speed
            motor2.running = False
            motor2.rpm = 0
            print(f"Motor2 below minimum speed: stopped, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    elif key == 'R':  # Motor 2 speed increase by 1 RPM
        motor2.rpm = min(motor2.rpm + RPM_STEP_SMALL, MAX_RPM)
        motor2.running = True
        print(f"Motor2 speed increased (1 RPM): {old_rpm2:.1f} -> {motor2.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    elif key == 'F':  # Motor 2 speed decrease by 1 RPM
        motor2.rpm = max(motor2.rpm - RPM_STEP_SMALL, 0)
        print(f"Motor2 speed decreased (1 RPM): {old_rpm2:.1f} -> {motor2.rpm:.1f} RPM, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
        if motor2.rpm == 0:
            motor2.running = False
        elif motor2.rpm < MIN_RPM:
            # Stop motor if below minimum speed
            motor2.running = False
            motor2.rpm = 0
            print(f"Motor2 below minimum speed: stopped, tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")
    
    # Control both motors together
    elif key == 'X':  # Stop all motors
        stop_all_motors()
    elif key == 'C':  # Reverse all motor directions
        reverse_all_directions()
    
    # Update only when not individual motor speed changes
    if key not in "QAWSEDRFP":  # P key doesn't update motors
        update_motor_speed(motor1, pwm1)
        update_motor_speed(motor2, pwm2)
    else:
        # For speed changes, update only the relevant motor
        if key in "QAED":
            update_motor_speed(motor1, pwm1)
        elif key in "WSRF":  # Exclude P key
            update_motor_speed(motor2, pwm2)
    
    # Output motor status (don't output for P key)
    if key != 'P':
        print(f"Motor1: {'running' if motor1.running else 'stopped'}, {motor1.rpm:.1f} RPM, direction: {'clockwise' if motor1.direction else 'counterclockwise'}")
        print(f"Motor2: {'running' if motor2.running else 'stopped'}, {motor2.rpm:.1f} RPM, direction: {'clockwise' if motor2.direction else 'counterclockwise'}")
        print(f"Tilt: X={current_angle_x:.1f}°, Y={current_angle_y:.1f}°")

# === Main execution ===
async def main():
    global pwm1, pwm2
    
    # PWM initialization
    init_pwm()
    
    # Execute motor control tasks
    usb_task = asyncio.create_task(usb_input_task())  # USB input handling
    mpu_task = asyncio.create_task(mpu6050_task())    # MPU6050 sensor measurement
    
    print(f"Initial settings - Recommended speed: {BASE_RPM} RPM, Max speed: {MAX_RPM} RPM, Min speed: {MIN_RPM} RPM")
    print(f"Motor1 current speed: {motor1.rpm:.1f} RPM, Motor2 current speed: {motor2.rpm:.1f} RPM")
    print(f"Microstepping: 1/{MICROSTEP} step")
    print(f"Min PWM frequency: {MIN_PWM_FREQ} Hz, Max PWM frequency: {MAX_PWM_FREQ} Hz")
    print("MPU6050 sensor measuring - Sampling period: 0.1 seconds")
    
    print("Key input guide:")
    print("Q/A: Motor1 speed 10 RPM increase/decrease")
    print("E/D: Motor1 speed 1 RPM increase/decrease")
    print("W/S: Motor2 speed 10 RPM increase/decrease")
    print("R/F: Motor2 speed 1 RPM increase/decrease")
    print("X: Stop both motors simultaneously")
    print("C: Reverse both motor directions simultaneously")
    print("P: Execute MPU6050 sensor calibration")
    
    try:
        last_print = time.time()
        while True:
            # Output current tilt status every 5 seconds
            now = time.time()
            if now - last_print >= 5:
                print(f"Current tilt - X-axis: {current_angle_x:.1f}°, Y-axis: {current_angle_y:.1f}°")
                last_print = now
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