import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

class YoloDetectionNode(Node):
    def __init__(self):
        super().__init__('yolo_detection_node')
        
        # 1. Load the AI Model (We use 'yolov8n' - the nano version for super fast real-time speeds)
        self.get_logger().info("Loading YOLOv8 AI Model...")
        self.model = YOLO('yolov8n.pt') 
        
        # 2. Tool to translate images between ROS 2 and OpenCV
        self.bridge = CvBridge()
        
        # 3. Subscribe to the camera's raw pictures
        self.subscription = self.create_subscription(
            Image,
            '/zed/rgb/image',
            self.image_callback,
            10)
            
        # 4. Create a publisher to broadcast the pictures WITH the AI boxes drawn on them
        self.publisher = self.create_publisher(Image, '/yolo/annotated_image', 10)
        
        self.get_logger().info("YOLOv8 Node is ready and waiting for images!")

    def image_callback(self, msg):
        # Convert the ROS 2 image into a standard OpenCV image
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        # Feed the image to the AI and tell it to look for objects
        results = self.model.track(cv_image, persist=True, tracker="bytetrack.yaml", verbose=False)      
        
        # Grab the image that has all the boxes and labels drawn on it automatically
        annotated_frame = results[0].plot()
        
        # Convert it back to a ROS 2 format and broadcast it to the robot
        annotated_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding="bgr8")
        annotated_msg.header = msg.header # Keep the exact same timestamp
        self.publisher.publish(annotated_msg)

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()