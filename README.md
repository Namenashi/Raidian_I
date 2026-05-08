<div align="center">
    <img src="Logo3-Icon-white.png" width="50%" alt="Logo">
</div>

### Overview
Raidian Unit 1, hereafter referred to as Unit 1, is a robot that I started developing with the goal of indoor and limited outdoor driving. The objectives are to drive using two wheels mounted parallel to each other, maintain balance through MPU6050 sensor and PID control, and transmit real-time captured video to users via a server.

<img src="Main.png" width="100%" alt="Main">

But mainly, there was two problems:
- The motor itself is the problem. The vibration is too severe. The vibration is so severe that even when the wheels aren't touching the ground - that is, when the robot body is supported and the wheels are spinning in the air - the sensor values jump tremendously due to excessive vibration. To solve this, we need a mechanism like suspension to prevent vibrations generated from the motor from being transmitted to the frame, which means the design itself needs to be modified from scratch.
- Motor control problem. The motor can't properly apply microstepping. It might be a problem with the motor driver. I don't know exactly where the problem is, but as a result, I can't control the motor finely enough for proper PID control to occur. But actually, that's not the biggest problem. The biggest issue related to this is the gear ratio. The gear ratio is too low, so at the motor's minimum speed that can actually be called "rotation," the wheel rotation speed is too fast. To solve this, there's no choice but to increase the gear ratio. The problem is that this also requires redesigning from scratch.

Therefore, I have decided to halt the development of this robot and build a new one, making use of the experience gained throughout this project.
While this ultimately became a failed project, I still want to organize the development process and the lessons learned from it. You can read a detailed deleopment log and Photos under my webpage:
https://namenashi.github.io/Webpage/