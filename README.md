# ROS 2 Distance Sensor and LED Alert (Raspberry Pi)

A small ROS 2 project for a Raspberry Pi. An HC-SR04 ultrasonic sensor measures distance and publishes it every 2 seconds. A second node listens to those readings and lights an LED when something is closer than 5 cm.

## How it works

```
HC-SR04 --> distance_publisher --/distance--> led_controller --> LED
                                     |
                                     +--> distance_subscriber (prints values)
```

| Node | What it does |
|------|--------------|
| `distance_publisher` | Reads the HC-SR04 on GPIO 23 and 24 and publishes the distance in cm to `/distance` every 2 seconds. |
| `led_controller` | Subscribes to `/distance` and turns the LED on GPIO 18 on when the distance is below the threshold. Turns the LED off if no readings arrive for 5 seconds. |
| `distance_subscriber` | Optional. Prints each received distance, to confirm messages are flowing. |

Topic: `/distance` (`std_msgs/msg/Float32`, centimetres)

## Hardware

| Part | Notes |
|------|-------|
| Raspberry Pi | Running 64-bit Ubuntu 22.04 (`uname -m` prints `aarch64`) |
| HC-SR04 ultrasonic sensor | Needs 5V |
| LED | Any standard 3 mm or 5 mm LED |
| 220 Ω resistor | In series with the LED |
| 1 kΩ and 2 kΩ resistors | Voltage divider on the sensor's ECHO pin |
| Breadboard and jumper wires | |

## Wiring

Shut the Pi down and unplug the power before wiring.

```
  RASPBERRY PI                                      HC-SR04
  +---------------+                                +-----------+
  | 5V     pin 2  |--------------------------------| VCC       |
  |               |                                |           |
  | GPIO23 pin 16 |--------------------------------| TRIG      |
  |               |                                |           |
  | GPIO24 pin 18 |-----------+------[ 1k ]--------| ECHO      |
  |               |           |                    |           |
  |               |         [ 2k ]                 |           |
  |               |           |                    |           |
  | GND    pin 6  |-----------+--------------------| GND       |
  |               |                                +-----------+
  | GPIO18 pin 12 |------[ 220 ]---->|------+
  |               |                 LED     |
  |               |                         |
  | GND    pin 14 |-------------------------+
  +---------------+
```

| Signal | Pi GPIO (BCM) | Physical pin | Connects to |
|--------|---------------|--------------|-------------|
| 5V | - | 2 | HC-SR04 VCC |
| TRIG | GPIO 23 | 16 | HC-SR04 TRIG |
| ECHO | GPIO 24 | 18 | HC-SR04 ECHO, through the voltage divider |
| Ground (sensor) | - | 6 | HC-SR04 GND and the bottom of the 2 kΩ resistor |
| LED | GPIO 18 | 12 | 220 Ω resistor, then the LED's long leg (anode) |
| Ground (LED) | - | 14 | LED's short leg (cathode) |

Notes:

- Physical pin 1 is the corner nearest the SD card slot. Odd pins are on the inner row and even pins on the outer edge row.
- The HC-SR04 ECHO pin outputs 5V, but Pi GPIO pins tolerate only 3.3V. The 1 kΩ and 2 kΩ resistors divide it down to about 3.3V. The Pi reads from the junction between them.
- The sensor and the Pi must share a ground, or readings will be erratic.
- The LED only works one way round. The long leg (anode) faces the resistor. Never connect it without the 220 Ω resistor.

## Software requirements

- Ubuntu 22.04 (64-bit) on the Pi
- ROS 2 Humble
- Python 3 with `RPi.GPIO` (use `rpi-lgpio` instead on a Pi 5)

## Installation

### 1. Install ROS 2 Humble

```bash
sudo apt install software-properties-common curl
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install ros-humble-ros-base python3-colcon-common-extensions python3-venv
```

If apt reports a lock error, Ubuntu is running background updates. Wait a few minutes and retry.

### 2. Create the Python environment

ROS's Python libraries are installed system-wide, so the environment must be able to see them:

```bash
source /opt/ros/humble/setup.bash
python3 -m venv --system-site-packages ~/ros_venv
source ~/ros_venv/bin/activate
pip install RPi.GPIO
```

On a Pi 5, run `pip install rpi-lgpio` instead. The code is unchanged.

### 3. Create the workspace and package

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python distance_pkg --dependencies rclpy std_msgs
```

Copy the node files into `distance_pkg/distance_pkg/` and register them in `setup.py`:

```python
    entry_points={
        'console_scripts': [
            'distance_publisher = distance_pkg.distance_publisher:main',
            'distance_subscriber = distance_pkg.distance_subscriber:main',
            'led_controller = distance_pkg.led_controller:main',
        ],
    },
```

### 4. Build

```bash
source /opt/ros/humble/setup.bash
source ~/ros_venv/bin/activate
cd ~/ros2_ws
colcon build --packages-select distance_pkg
source install/setup.bash
```

Build with the venv active so the installed commands use its Python (with `RPi.GPIO`). Use `colcon build --symlink-install` if you want Python edits to apply without rebuilding.

## Project structure

```
~/ros2_ws/
└── src/
    └── distance_pkg/
        ├── package.xml                  package name, version, dependencies
        ├── setup.py                     build script and node entry points
        ├── setup.cfg                    install locations (leave as generated)
        ├── resource/distance_pkg        marker file that registers the package
        ├── test/                        generated style checks
        └── distance_pkg/
            ├── __init__.py              makes the folder a Python package
            ├── distance_publisher.py    reads the sensor, publishes /distance
            ├── distance_subscriber.py   prints received distances (optional)
            └── led_controller.py        drives the LED from /distance
```

## Usage

Every new terminal needs these three lines first:

```bash
source /opt/ros/humble/setup.bash
source ~/ros_venv/bin/activate
source ~/ros2_ws/install/setup.bash
```

Terminal 1, the sensor:

```bash
ros2 run distance_pkg distance_publisher
```

Terminal 2, the LED:

```bash
ros2 run distance_pkg led_controller
```

Optional, print the readings:

```bash
ros2 run distance_pkg distance_subscriber
```

Move your hand within 5 cm of the sensor and the LED lights on the next reading. It turns off when you move away.

Useful checks:

```bash
ros2 topic list             # /distance should appear
ros2 topic echo /distance   # live values
ros2 topic hz /distance     # should be about 0.5 Hz
```

## Configuration

| Setting | Default | How to change |
|---------|---------|---------------|
| LED threshold | 5.0 cm | `ros2 run distance_pkg led_controller --ros-args -p threshold_cm:=10.0` |
| Watchdog timeout | 5.0 s | `--ros-args -p timeout_s:=8.0` |
| Publish rate | 2 s | Change `create_timer(2.0, ...)` in `distance_publisher.py` |
| Pins | 23, 24, 18 | Change `TRIG`, `ECHO` and `LED_PIN` at the top of each file |

## Testing without the sensor

To check the LED wiring and node on their own, run only `led_controller` and publish fake readings from another terminal:

```bash
ros2 topic pub --once /distance std_msgs/msg/Float32 "{data: 3.0}"    # LED on
ros2 topic pub --once /distance std_msgs/msg/Float32 "{data: 20.0}"   # LED off
```

## Troubleshooting

| Problem | Likely cause and fix |
|---------|----------------------|
| `No module named 'rclpy'` | Run `source /opt/ros/humble/setup.bash`, and make sure the venv was created with `--system-site-packages`. |
| `No module named 'RPi'` | The package was built without the venv active. Activate it, delete `build/ install/ log/`, and rebuild. |
| GPIO permission or `/dev/mem` error | Ubuntu restricts GPIO for normal users. Add your user to the `gpio` group if it exists (`sudo usermod -aG gpio $USER`, then log out and in), or run the node with `sudo` using the venv's Python. |
| `Not running on a RPi!` or GPIO import errors on a Pi 5 | Replace `RPi.GPIO` with `rpi-lgpio`. |
| Publisher always logs "No reading from sensor" | Check that VCC is on 5V, the grounds are shared, TRIG and ECHO are not swapped, and the divider is wired correctly. |
| LED never lights, even with fake messages | Check the LED direction, the 220 Ω resistor, and that it is on physical pin 12, not pin 18. |
| LED lights, then turns off after about 5 s | The watchdog fired because readings stopped. Check the publisher terminal for warnings. |
| ROS nodes on two machines can't see each other | Use the same `ROS_DOMAIN_ID` and the same network. Guest networks that isolate devices block ROS traffic. |
| Repeated crashes or Wi-Fi drops | Check power with `vcgencmd get_throttled` (should be `0x0`) and use a good SD card. |

## Safety

- Never connect the HC-SR04 ECHO pin straight to a GPIO pin. Use the voltage divider.
- Always use a series resistor with the LED.
- Power the Pi off before changing wiring.

## License

Add your license here (for example MIT).
