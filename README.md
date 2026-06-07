# px4-yolo-ros2

A ROS2 package for real-time object detection on a PX4-powered drone using YOLOv8 and Gazebo simulation.

The drone streams camera footage through Gazebo, bridges it to ROS2, and runs YOLOv8 inference on every frame — publishing annotated images with bounding boxes to a ROS2 topic.

---

## Stack

| Component | Version |
|---|---|
| OS | Ubuntu 24.04 |
| ROS2 | Jazzy |
| PX4 Autopilot | SITL (Software In The Loop) |
| Simulator | Gazebo (gz-sim) |
| Bridge (PX4 ↔ ROS2) | Micro XRCE-DDS Agent |
| Bridge (Gazebo ↔ ROS2) | ros_gz_bridge |
| Detection model | YOLOv8n (Ultralytics) |

---

## Project Structure

```
ros2_ws/
└── src/
    └── OD/
        ├── OD/
        │   └── yolo_node.py          # YOLO inference node
        ├── launch/
        │   └── object_detection.launch.py  # Main launch file
        ├── package.xml
        └── setup.py
```

---

## Prerequisites

### 1. ROS2 Jazzy
Follow the official installation guide:
https://docs.ros.org/en/jazzy/Installation.html

### 2. PX4 Autopilot
```bash
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
bash ./Tools/setup/ubuntu.sh
```

### 3. Micro XRCE-DDS Agent
```bash
git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent && mkdir build && cd build
cmake ..
make
sudo make install
sudo ldconfig /usr/local/lib/
```

### 4. Gazebo + ROS bridge
```bash
sudo apt install ros-jazzy-ros-gz
sudo apt install ros-jazzy-ros-gz-bridge
```

### 5. Python dependencies
```bash
pip install ultralytics opencv-python torch
sudo apt install ros-jazzy-cv-bridge
```

---

## Installation

```bash
# Clone into your ROS2 workspace
cd ~/ros2_ws/src
git clone https://github.com/YOUR_USERNAME/px4-yolo-ros2.git OD

# Build
cd ~/ros2_ws
colcon build --packages-select OD
source install/setup.bash
```

---

## Running a Demo

The demo requires two terminals — one for the PX4+Gazebo simulation, one for the ROS2 stack.

### Terminal 1 — Start PX4 SITL with Gazebo

```bash
cd ~/PX4-Autopilot
make px4_sitl gz_x500_mono_cam
```

Wait until Gazebo is fully loaded and the drone model appears before proceeding.

### Terminal 2 — Launch the ROS2 stack

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch OD object_detection.launch.py
```

This single command starts:
1. **Micro XRCE-DDS Agent** — bridges PX4 with ROS2 over UDP
2. **ros_gz_bridge** — forwards the Gazebo camera topic to ROS2
3. **YOLO node** — runs object detection and publishes annotated frames

### Verify it's working

```bash
# Check topics are live
ros2 topic list | grep camera

# Check inference output
ros2 topic echo /camera/yolo_detected --no-arr

# Watch inference latency in the launch terminal — you should see:
# [YOLO] latency: XXX ms | device: CPU | detections: N | labels: [...]
```

### Visualize in RViz2

```bash
rviz2
```

Add an **Image** display and set the topic to `/camera/yolo_detected`.

---

## Topics

| Topic | Type | Direction | Description |
|---|---|---|---|
| `/camera` | `sensor_msgs/msg/Image` | Gazebo → ROS2 | Raw camera stream |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Gazebo → ROS2 | Camera calibration info |
| `/camera/yolo_detected` | `sensor_msgs/msg/Image` | ROS2 publish | Annotated frames with bounding boxes |

---

## Configuration

| Parameter | Location | Default |
|---|---|---|
| DDS UDP port | `object_detection.launch.py` | `8888` |
| YOLO model path | `yolo_node.py` | **see below** |
| Confidence threshold | `yolo_node.py` | `0.1` |

### ⚠️ Set your YOLO model path

Before running, open `OD/yolo_node.py` and update this line with the absolute path to your own `.pt` model file:

```python
self.model = YOLO('/absolute/path/to/your/model.pt')
```

Example:
```python
self.model = YOLO('/home/YOUR_USERNAME/ros2_ws/src/OD/OD/your_model.pt')
```

The model file is not included in this repository (excluded via `.gitignore`).  
Supply your own YOLOv8 model — either custom trained or a pretrained one from [Ultralytics](https://docs.ultralytics.com/models/yolov8).

To change the DDS port at runtime:
```bash
ros2 launch OD object_detection.launch.py dds_port:=9999
```

---

## License

MIT
