import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

# Import your brand new custom messages!
from slam_msgs.msg import Detection, DetectionArray

class YoloDetectionNode(Node):
    def __init__(self):
        super().__init__('yolo_detection_node')
        
        # Load the lightning-fast TensorRT engine we built
        self.get_logger().info("Loading YOLOv8 TensorRT Engine...")
        self.model = YOLO('/home/diksha/slam_ws/models/yolov8m.engine', task='detect') 
        
        self.bridge = CvBridge()
        
        self.subscription = self.create_subscription(
            Image, '/zed/rgb/image', self.image_callback, 10)
            
        # We now publish the math array, not just the image
        self.detection_pub = self.create_publisher(DetectionArray, '/yolo/detections', 10)
        self.image_pub = self.create_publisher(Image, '/yolo/annotated_image', 10)
        
        self.get_logger().info("YOLOv8 Tracking Node is running!")

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        
        # Run inference with ByteTrack enabled
        results = self.model.track(cv_image, persist=True, tracker="bytetrack.yaml", verbose=False)
        
        # Create our custom array message
        det_array_msg = DetectionArray()
        det_array_msg.header = msg.header # Keep exact timestamp
        
        # Extract the raw math for every object detected
        if results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                det_msg = Detection()
                
                # Bounding box coordinates [x1, y1, x2, y2]
                xyxy = boxes.xyxy[i].cpu().numpy()
                det_msg.bbox_x1 = float(xyxy[0])
                det_msg.bbox_y1 = float(xyxy[1])
                det_msg.bbox_x2 = float(xyxy[2])
                det_msg.bbox_y2 = float(xyxy[3])
                
                # Confidence and Class
                det_msg.confidence = float(boxes.conf[i].cpu().numpy())
                det_msg.class_id = int(boxes.cls[i].cpu().numpy())
                det_msg.class_name = self.model.names[det_msg.class_id]
                
                # ByteTrack ID (If the tracker loses it briefly, it might be None)
                if boxes.id is not None:
                    det_msg.track_id = int(boxes.id[i].cpu().numpy())
                else:
                    det_msg.track_id = -1
                    
                det_array_msg.detections.append(det_msg)
                
        # Broadcast the raw data to the ROS 2 network
        self.detection_pub.publish(det_array_msg)
        
        # (Optional) Still publish the annotated image for visual debugging
        annotated_frame = results[0].plot()
        annotated_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding="bgr8")
        annotated_msg.header = msg.header
        self.image_pub.publish(annotated_msg)

def main(args=None):
    rclpy.init(args=args)
    node = YoloDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()