<div align="center">
    <img src="Logo/Logo3-Icon.png" width="50%" alt="Logo">
</div>

# Pilot Unit: Raidian I Development Log
I'm an Informatik (Computer Science) student with no robotics knowledge beyond basic Arduino tutorials. This document should be viewed as an amateur's failure log and a record of gradually gaining experience through those failures. 
Claude was used during the writing process to help with grammar and corrections.

<img src="Photo/Raidian_I/Main.png" alt="Main">

### Overview
Raidian Unit 1, hereafter referred to as Unit 1, is a robot that I started developing with the goal of indoor and limited outdoor driving. The objectives are to drive using two wheels mounted parallel to each other, maintain balance through MPU6050 sensor and PID control, and transmit real-time captured video to users via a server.
This unit also serves as a pilot model for future development. Through completing this unit, I expect to reconfirm my current abilities, establish and optimize the overall development process to some extent, and learn solutions to non-theoretical problems that will be encountered in actual robot development, in addition to theoretical aspects.
While this ultimately became a failed project, I still want to organize the development process and the lessons learned from it.

### Problems of Previous Versions
The very first ver.1 I built didn't work properly due to insufficient performance of the stepper motors I used, contrary to expectations at the time of manufacture. To solve this problem, I made ver.2 with larger motors, but like ver.1, it was composed of PLA parts made with a 3D printer. The area around the motor driver couldn't withstand the heat from the changed stepper motor driver and started warping. To fix this, I made ver.3 by adding 6 coolers, increasing part thickness, adding functional components like switches, and changing the wheel drive system to rotate along rails inside the wheel, among other modifications. However:

- The mechanical durability of the PLA body that's hard to trust, even with reinforcement using M3 Gewindestange
- Impossible mounting of additional modules or loading of objects due to the robot's design and mechanical structure
- PLA drive components like gears can't withstand even half of the motor's maximum torque, and considering the durability decrease due to heat from motors or motor drivers, they can ultimately only handle an extremely small portion of the motor's torque
- Moreover, high-speed driving itself would be impossible due to these material durability limits

Since I couldn't solve these fundamental problems caused by the limitations of materials used in robot construction, I decided to start making a new version.

<img src="Photo/Raidian_I/Ver3/PXL_20241028_191448858.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241028_191507113.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241029_215002638.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241030_103023779.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241029_153633618.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241101_011754470.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241113_232816917.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241102_141401536.jpg" alt="Image">
<img src="Photo/Raidian_I/Ver3/PXL_20241113_234714605.jpg" alt="Image">


### Before Making ver.4. Improvements I Wanted to Apply
- 3D printing is certainly useful in many ways, allowing the creation of various shaped parts, but full 3D printing body construction has many problems mainly in strength and heat resistance (no matter how much attention is paid to printing direction or layer adhesion). As methods to somewhat improve this, I tried inserting gewindestange for reinforcement or dividing into as few parts as possible this time, and I think there was some degree of success, but it's not a fundamental solution. Moreover, the Gewindestange insertion method increases overall weight and makes assembly and maintenance processes difficult, and making parts as large as possible similarly increases overall weight and the amount of wasted support PLA, takes longer printing time, and seems to make part replacement, assembly, and maintenance difficult. It might be my lack of skill though.
- Using other materials like ABS might make a difference, but that's troublesome to use at home, plus it shrinks severely, so I personally think it's even less suitable for this purpose.
- Let's avoid using Gewinde parts that are melted and inserted for fixing as much as possible. The precision tends to drop during insertion (especially angles), resulting in parts not fitting well together. And while the inserted threads are stronger than expected, they're still not strong enough to have high expectations. I think it's better to just use conventional bolt-nut fixing methods when possible.
- It seems better to avoid painting when possible. Production time increases exponentially, and the results aren't very satisfying either. While there might be merit in terms of weight, the smell is very strong, and if this much effort and space is needed for painting a body of this size, it seems hard to handle if it gets bigger. Most importantly, since I find it annoying and hate spending days painting, let's finish with film when possible and only paint unavoidable parts from now on. But thinking conversely, film finishing also seems difficult to use on PLA material due to the characteristic of needing to be attached while heating, and I expect it would be hard to finish non-flat parts with film, so painting might be more suitable at times like this. Let's choose according to the situation.

<img src="Photo/Raidian_I_Render/Cubli alt 2 v24 2.png" alt="Image">
<img src="Photo/Raidian_I_Render/Cubli alt 2 v34 4.png" alt="Image">
<img src="Photo/Raidian_I_Render/Cubli alt 2 v24.png" alt="Image">
<img src="Photo/Raidian_I_Render/Cubli alt 2 v24 3.png" alt="Image">
<img src="Photo/Raidian_I_Render/Cubli alt 2 v34 5.png" alt="Image">
<img src="Photo/Raidian_I_Render/Screenshot 2024-11-25 111722.png" alt="Image">
<img src="Photo/Raidian_I_Render/Screenshot 2024-11-25 111634.png" alt="Image">

### About Robot Specs and Component Selection
- Will uns ESP32.
- The robot's total weight is conservatively estimated at around 10kg for now.
Using solid rubber tires (Vollgummireifen) for electric scooters as tires. Accordingly, the wheels will also be those made for electric scooters (specifically rear wheels).
- Since these aren't products made with the premise of being used as drive wheels, I plan to use keyless bushes to connect them to the shaft and transmit power.
- The motor will be a stepper motor with specs: 57MM44A76, step angle 1.8°, rated current 4.4A, holding torque 2.3Nm, used with microstep 8 setting. This will enable control in 0.225° increments.
- The gear ratio will be 1:2 reduction. This time I plan to implement it using spur gears. It's simpler than chain and sprocket systems, smaller in size, and most importantly, can be made at a lower cost.
- The main frame will be made using 2020 aluminum frame that I bought but didn't use, maximizing its utilization.
- I want to keep the budget for this new version within 200 Euro. I'll use existing parts as much as possible and avoid additional expenses.
- As an important upgrade point from the previous version, let's improve accessibility to the microprocessor and main control components. My current thought is to fix them at the top and make that part completely openable. Actually, I think Raspberry Pi or Arduino won't have severe heating issues and can be mounted on PLA parts without problems. I'll mount the battery and motor drivers on aluminum profiles.
- I plan to use the existing 4S4P battery as is. I haven't thought about the location, but I'm thinking of placing it at the bottom as much as possible.
- Another major change is changing the robot's exterior color to a combination of navy blue and white with black accents. I think the gray and white combination wasn't good.
- I plan to make it capable of stable driving in the 10-15km/h speed range and up to 20km/h driving under limited time and appropriate acceleration conditions.
- Since I expect the need to overcome vibration, let's also use Federscheibe (spring washers).

<img src="Photo/Raidian_I/PXL_20241206_121831338.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241206_203218588.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241209_181803304.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241211_143746908.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241211_192512382.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241211_192546159.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241212_175523942.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241216_145513824.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241218_233348821.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241219_024019181.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241219_035544739.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241224_091721130.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241229_155106554.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20241229_155122162.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250101_135740969.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250118_203126183.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250120_020847239.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250120_035920067.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250121_044917657.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250124_232619370.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250129_054546298.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250129_121938738.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250201_151037226.jpg" alt="Image">
<img src="Photo/Raidian_I/PXL_20250202_162843249.jpg" alt="Image">

### ESP32 Pin Map
- MPU 6050 SDA -> GPIO 21
- MPU 6050 SCL -> GPIO 22
- NTC 1 ESP -> GPIO 35
- NTC 2 Stepdown -> GPIO 34
- NTC 3 Motor L -> GPIO 32
- NTC 4 Motor R -> GPIO 33
- Driver 1 Step -> GPIO 27
- Driver 1 DIR -> GPIO 26
- Driver 1 EN -> GPIO 25
- Driver 2 Step -> GPIO 15
- Driver 2 DIR -> GPIO 4
- Driver 2 EN -> GPIO 5
- TX -> GPIO 17
- RX -> GPIO 16

### After Project Termination
I think there's no significant meaning in holding onto this any longer. So, let's end the project here.
There are mainly two problems:

- The motor itself is the problem. The vibration is too severe. The vibration is so severe that even when the wheels aren't touching the ground - that is, when the robot body is supported and the wheels are spinning in the air - the sensor values jump tremendously due to excessive vibration. To solve this, we need a mechanism like suspension to prevent vibrations generated from the motor from being transmitted to the frame, which means the design itself needs to be modified from scratch. We basically have to remake it.
- Motor control problem. The motor can't properly apply microstepping. It might be a problem with the motor driver. I don't know exactly where the problem is, but as a result, I can't control the motor finely enough for proper PID control to occur. But actually, that's not the biggest problem. The biggest issue related to this is the gear ratio. The gear ratio is too low, so at the motor's minimum speed that can actually be called "rotation," the wheel rotation speed is too fast. To solve this, there's no choice but to increase the gear ratio. The problem is that this also requires redesigning from scratch.

This project didn't produce results. But, I learned a lot:

- When testing motors(or other things), test them under the expected load. When I first tested just the motor for testing purposes, the vibration wasn't as severe as it is now (with load from wheels and gears).
- Be especially careful with gear ratio settings. I think this problem would be relatively less of a concern if using something like BLDC, but if using stepper motors, you shouldn't think that motor's minimum operating speed = motor's minimum speed for continuous rotation. When considering gear ratios, you should base it on the motor's minimum speed for continuous rotation without stopping, not the motor's minimum operating speed.
- Suspension is important. For devices like motors or wheels that inevitably generate vibration, you must install suspension or shock absorbers to prevent that vibration or impact from being transmitted directly to the frame.
- Battery system design requires sufficient attention. Especially BMS selection. Buy reliable components. The upper limit that the BMS can output is important. And when I say upper limit, I don't mean the theoretical maximum, then the upper limit of output that can be sustained continuously.
- Installing cooling fans itself was a good idea. Just consider air flow next time. Placing components that both generate heat, like motors and controllers, on the same line and cooling the next component with air that cooled the previous one doesn't seem like a very good idea.
- Installing LEDs is good. And it looks cool too. It's good to install them, but make sure to check whether that LED light enters the camera. In this design too, LEDs were mounted next to the camera, but LED light entered the camera, causing the phenomenon where both ends of the camera image were filmed in blue. This time it was okay since I didn't reach the level of recognizing surrounding environment through the camera, but if I had reached that point, I expect this phenomenon would have likely caused problems with object recognition through the camera.
- Be careful with tire selection too. Outdoor tires aren't suitable for indoor driving. Especially if there's no sufficient shock absorption mechanism.

### Videos
- <https://youtu.be/-DF1HXfhPAE>
- <https://youtu.be/lkxy4-hASk0>
- <https://youtu.be/9Nc2mmjC67E>
- <https://youtu.be/tmr79TZlkPo>
- <https://youtu.be/xLNv38b5Bgc>
