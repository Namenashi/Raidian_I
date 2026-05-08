from machine import Pin, I2C
import math
import time

# MPU6050 setup
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
mpu_addr = 0x68

# MPU6050 register addresses
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# Complementary filter settings
COMPLEMENTARY_WEIGHT = 0.95
SAMPLING_TIME = 0.1  # 100ms

# Calibration offset values (replace with your actual measured values)
accel_offset_x = 1154.82
accel_offset_y = -183.27
accel_offset_z = 897.24
gyro_offset_x = -321.26
gyro_offset_y = 23.67
gyro_offset_z = 105.07

def init_mpu6050():
    """Initialize MPU6050"""
    try:
        # Set power management register (wake up from sleep mode)
        i2c.writeto_mem(mpu_addr, PWR_MGMT_1, bytes([0]))
        time.sleep_ms(100)  # Wait for initialization
        print("MPU6050 initialization successful")
        return True
    except Exception as e:
        print(f"MPU6050 initialization failed: {e}")
        return False

def read_raw_data(addr):
    """Read 2-byte raw data from register"""
    high = i2c.readfrom_mem(mpu_addr, addr, 1)[0]
    low = i2c.readfrom_mem(mpu_addr, addr + 1, 1)[0]
    value = (high << 8) | low
   
    # Two's complement processing (16-bit negative number handling)
    if value > 32767:
        value -= 65536
    return value

def read_mpu6050():
    """Read acceleration and gyro data from MPU6050 (with calibration applied)"""
    try:
        # Read accelerometer values
        accel_x = read_raw_data(ACCEL_XOUT_H) - accel_offset_x
        accel_y = read_raw_data(ACCEL_XOUT_H + 2) - accel_offset_y
        accel_z = read_raw_data(ACCEL_XOUT_H + 4) - accel_offset_z
       
        # Read gyroscope values
        gyro_x = read_raw_data(GYRO_XOUT_H) - gyro_offset_x
        gyro_y = read_raw_data(GYRO_XOUT_H + 2) - gyro_offset_y
        gyro_z = read_raw_data(GYRO_XOUT_H + 4) - gyro_offset_z
       
        # Convert acceleration values (in g units)
        ax = accel_x / 16384.0
        ay = accel_y / 16384.0
        az = accel_z / 16384.0
       
        # Convert gyro values (in degrees/second)
        gx = gyro_x / 131.0
        gy = gyro_y / 131.0
        gz = gyro_z / 131.0
       
        return ax, ay, az, gx, gy, gz
    except Exception as e:
        print(f"MPU6050 data reading error: {e}")
        return 0, 0, 0, 0, 0, 0

def calculate_angle(ax, ay, az, gx, prev_angle, dt):
    """Calculate X-axis tilt angle using complementary filter"""
    # Calculate X-axis angle from accelerometer (convert from radians to degrees)
    accel_angle = math.atan2(ay, az) * 180 / math.pi
   
    # Calculate angle change from gyro measurement (degrees/second * seconds = degrees)
    gyro_angle = prev_angle + gx * dt
   
    # Apply complementary filter
    angle = COMPLEMENTARY_WEIGHT * gyro_angle + (1 - COMPLEMENTARY_WEIGHT) * accel_angle
   
    # Handle both -0 and 0 as 0
    if angle == -0.0 or angle == 0.0:
        angle = 0.00
       
    return angle

def main():
    if not init_mpu6050():
        return
   
    # Initial angle (0)
    angle_x = 0
   
    # Store previous time
    last_time = time.time()
   
    print("Measurement started... (Exit: Ctrl+C)")
    try:
        while True:
            # Calculate current time and elapsed time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
           
            # Read sensor data (with calibration applied)
            ax, ay, az, gx, gy, gz = read_mpu6050()
           
            # Calculate X-axis tilt angle (using complementary filter)
            angle_x = calculate_angle(ax, ay, az, gx, angle_x, dt)
           
            # Output angle
            print(f"X-axis tilt: {angle_x:.2f}°")
           
            # Maintain sampling interval
            time.sleep(SAMPLING_TIME)
    except KeyboardInterrupt:
        print("Program terminated")

if __name__ == "__main__":
    main()