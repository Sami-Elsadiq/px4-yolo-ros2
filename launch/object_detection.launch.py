import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    TimerAction,
    LogInfo,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # ── Launch Arguments ──────────────────────────────────────────────────────

    dds_port_arg = DeclareLaunchArgument(
        "dds_port",
        default_value="8888",
        description="UDP port for the Micro XRCE-DDS Agent",
    )

    # ── 1. Micro XRCE-DDS Agent  (PX4 ↔ ROS2 bridge) ────────────────────────

    micro_dds_agent = ExecuteProcess(
        cmd=[
            "MicroXRCEAgent",
            "udp4",
            "-p",
            LaunchConfiguration("dds_port"),
        ],
        name="micro_xrce_dds_agent",
        output="screen",
        # Uncomment the next line if the agent binary is not on $PATH
        # and you need to run it from its build directory:
        # cwd=LaunchConfiguration("dds_agent_path"),
    )

    # ── 2. ros_gz_bridge  (Gazebo camera → ROS2) ─────────────────────────────
    #
    # Format:  <gz_topic>@<ros_type>[<gz_type>
    #   [  = Gazebo → ROS2   (unidirectional)
    #   ]  = ROS2  → Gazebo  (unidirectional)
    #   @  = bidirectional
    #
    # We bridge:
    #   • raw image
    #   • camera_info  (needed by most vision pipelines)

    gz_ros_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="camera_bridge",
        output="screen",
        arguments=[
            # image stream  (Gazebo → ROS2)
            "/camera@sensor_msgs/msg/Image[gz.msgs.Image",
            # camera info   (Gazebo → ROS2)
            "/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
        ],
        # Remap Gazebo topic names to your preferred ROS2 names if they differ
        # remappings=[
        #     ("/camera", "/drone/camera/image_raw"),
        # ],
    )

    # ── 3. YOLO flag-detection node ───────────────────────────────────────────
    #
    # Package: OD  |  executable: yolo_node  (as declared in setup.py)
    # The node hardcodes its model path and subscribes to /camera internally,
    # so no extra parameters are needed here.

    yolo_detector_node = Node(
        package="OD",
        executable="yolo_node",
        name="yolo_node",
        output="screen",
    )

    # ── Startup sequencing ────────────────────────────────────────────────────
    #
    # Give the DDS agent a couple of seconds to bind its socket before the
    # bridge and detector come up.  Adjust the delays to match your hardware.

    delayed_bridge = TimerAction(period=2.0, actions=[gz_ros_bridge])
    delayed_detector = TimerAction(period=4.0, actions=[yolo_detector_node])

    return LaunchDescription(
        [
            # Arguments
            dds_port_arg,
            # Processes / nodes
            LogInfo(msg="[1/3] Starting Micro XRCE-DDS Agent…"),
            micro_dds_agent,
            LogInfo(msg="[2/3] Starting Gazebo→ROS2 camera bridge (delay 2 s)…"),
            delayed_bridge,
            LogInfo(msg="[3/3] Starting YOLO flag-detector node (delay 4 s)…"),
            delayed_detector,
        ]
    )
