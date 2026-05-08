from machine import Pin, I2C
import time

# MPU6050 setup
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
mpu_addr = 0x68

# MPU6050 register addresses
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

def init_mpu6050():
    """Initialize MPU6050"""
    i2c.writeto_mem(mpu_addr, PWR_MGMT_1, bytes([0]))
    time.sleep_ms(100)
    print("MPU6050 initialization complete")

def read_raw_data(addr):
    """Read 2-byte raw data from register"""
    high = i2c.readfrom_mem(mpu_addr, addr, 1)[0]
    low = i2c.readfrom_mem(mpu_addr, addr + 1, 1)[0]
    value = (high << 8) | low
   
    # Two's complement processing
    if value > 32767:
        value -= 65536
    return value

def calibrate_mpu6050(samples=1000):
    """MPU6050 sensor calibration"""
    print("MPU6050 calibration starting...")
    print("Place the sensor on a flat surface and do not move it...")
    time.sleep(2)  # Time for user to stabilize the sensor
   
    # Calibration initialization
    accel_offset_x = accel_offset_y = accel_offset_z = 0
    gyro_offset_x = gyro_offset_y = gyro_offset_z = 0
   
    # Collect multiple samples
    for i in range(samples):
        accel_x = read_raw_data(ACCEL_XOUT_H)
        accel_y = read_raw_data(ACCEL_XOUT_H + 2)
        accel_z = read_raw_data(ACCEL_XOUT_H + 4)
       
        gyro_x = read_raw_data(GYRO_XOUT_H)
        gyro_y = read_raw_data(GYRO_XOUT_H + 2)
        gyro_z = read_raw_data(GYRO_XOUT_H + 4)
       
        accel_offset_x += accel_x
        accel_offset_y += accel_y
        accel_offset_z += accel_z
       
        gyro_offset_x += gyro_x
        gyro_offset_y += gyro_y
        gyro_offset_z += gyro_z
       
        if i % 100 == 0:
            print(f"Collecting samples: {i}/{samples}")
       
        time.sleep_ms(5)
   
    # Calculate average values
    accel_offset_x /= samples
    accel_offset_y /= samples
    accel_offset_z /= samples
    gyro_offset_x /= samples
    gyro_offset_y /= samples
    gyro_offset_z /= samples
   
    # Z-axis acceleration gravity (1g) compensation
    accel_offset_z -= 16384  # Value corresponding to 1g in 2g range
   
    print("\n===== Calibration Results =====")
    print(f"Accelerometer offsets: X={accel_offset_x:.2f}, Y={accel_offset_y:.2f}, Z={accel_offset_z:.2f}")
    print(f"Gyroscope offsets: X={gyro_offset_x:.2f}, Y={gyro_offset_y:.2f}, Z={gyro_offset_z:.2f}")
    print("===============================")
   
    return {
        'accel_offset_x': accel_offset_x,
        'accel_offset_y': accel_offset_y,
        'accel_offset_z': accel_offset_z,
        'gyro_offset_x': gyro_offset_x,
        'gyro_offset_y': gyro_offset_y,
        'gyro_offset_z': gyro_offset_z
    }

# Main execution
init_mpu6050()
offsets = calibrate_mpu6050()

# Example usage of calibration values
print("\nCopy the values below to use in your code:")
print(f"accel_offset_x = {offsets['accel_offset_x']:.2f}")
print(f"accel_offset_y = {offsets['accel_offset_y']:.2f}")
print(f"accel_offset_z = {offsets['accel_offset_z']:.2f}")
print(f"gyro_offset_x = {offsets['gyro_offset_x']:.2f}")
print(f"gyro_offset_y = {offsets['gyro_offset_y']:.2f}")
print(f"gyro_offset_z = {offsets['gyro_offset_z']:.2f}")