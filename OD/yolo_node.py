import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np
import torch


class YoloNode(Node):
    def __init__(self):
        super().__init__('yolo_node')
        self.bridge = CvBridge()

        # ── Device selection ──────────────────────────────────────────────────
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.get_logger().info(f'Running inference on: {self.device.upper()}')

        # ── Load model ────────────────────────────────────────────────────────
        self.model = YOLO('/home/sami/ros2_ws/src/OD/OD/flag_detection_yv8n.pt')
        self.model.to(self.device)

        # ── Warm up: absorbs the slow first-inference cost before real frames ─
        # Without this, the very first frame your drone sees takes 3-5x longer
        # than all subsequent ones (GPU memory allocation, kernel JIT compile).
        dummy = np.zeros((480, 640, 3), dtype=np.uint8)
        self.model(dummy, verbose=False)
        self.get_logger().info('Model warmed up — ready.')

        # ── Frame-drop guard ──────────────────────────────────────────────────
        self._processing = False

        # ── Queue depth 1: always process the LATEST frame ───────────────────
        self.sub = self.create_subscription(
            Image,
            '/camera',
            self.image_callback,
            1,
        )

        # ── Publisher ─────────────────────────────────────────────────────────
        self.pub = self.create_publisher(Image, '/camera/yolo_detected', 1)
        self.class_names = self.model.names

    def image_callback(self, msg):
        # Drop frame if previous inference is still running.
        if self._processing:
            return
        self._processing = True

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

            # verbose=False suppresses per-frame stdout (I/O blocks the thread).
            # All other parameters unchanged — no accuracy tradeoff.
            t_start = self.get_clock().now()
            results = self.model(
                cv_image,
                conf=0.1,
                verbose=False,
                device=self.device,
            )
            latency_ms = (self.get_clock().now() - t_start).nanoseconds / 1e6

            detections = results[0].boxes
            labels = (
                [self.class_names[int(b.cls)] for b in detections]
                if detections is not None and len(detections) > 0
                else []
            )
            self.get_logger().info(
                f'[YOLO] latency: {latency_ms:.1f} ms | '
                f'device: {self.device.upper()} | '
                f'detections: {len(labels)} | '
                f'labels: {labels if labels else "none"}'
            )

            # Skip annotation rendering when no subscriber is active.
            # results[0].plot() is surprisingly expensive — no point running it
            # if nothing is listening (e.g. RViz2 is closed).
            if self.pub.get_subscription_count() > 0:
                annotated = results[0].plot()
                out_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
                out_msg.header = msg.header  # preserve original timestamp
                self.pub.publish(out_msg)

        except Exception as e:
            self.get_logger().error(f'Inference error: {e}')
        finally:
            self._processing = False


def main(args=None):
    rclpy.init(args=args)
    node = YoloNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
