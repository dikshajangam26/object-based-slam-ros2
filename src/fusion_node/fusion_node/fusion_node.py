import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from slam_msgs.msg import DetectionArray
import message_filters
from cv_bridge import CvBridge
import numpy as np

class FusionNode(Node):
    def __init__(self):
        super().__init__('fusion_node')
        self.bridge = CvBridge()
        
        # Camera Intrinsics from Task 1.5 (Isaac Sim ZED 2 HD720 configuration)
        self.fx = 528.0
        self.fy = 528.0
        self.cx = 640.0
        self.cy = 360.0
        
        # TASK 2.5: Central Object Registry
        self.object_registry = {}
        self.max_history_len = 10 # Keep tracking the last 10 bounding boxes
        
        # Synchronized subscribers for AI detections and Depth Map
        self.det_sub = message_filters.Subscriber(self, DetectionArray, '/yolo/detections')
        self.depth_sub = message_filters.Subscriber(self, Image, '/zed/depth/image')
        
        # Match data frames within 100ms threshold
        self.ts = message_filters.ApproximateTimeSynchronizer([self.det_sub, self.depth_sub], queue_size=10, slop=0.1)
        self.ts.registerCallback(self.fusion_and_registry_callback)
        
        self.get_logger().info("Sensor Fusion & Object State Registry Node is active!")

    def fusion_and_registry_callback(self, det_msg, depth_msg):
        # Convert ROS image to OpenCV float32 depth map (values are in meters)
        depth_map = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='32FC1')
        
        current_frame_tracks = set()
        
        for det in det_msg.detections:
            track_id = det.track_id
            if track_id == -1:
                continue # Skip untracked detections
                
            current_frame_tracks.add(track_id)
            
            # 1. Compute bounding box parameters
            bbox = [det.bbox_x1, det.bbox_y1, det.bbox_x2, det.bbox_y2]
            u_center = int((det.bbox_x1 + det.bbox_x2) / 2)
            v_center = int((det.bbox_y1 + det.bbox_y2) / 2)
            
            # 2. Extract and validate depth from center pixel
            # Safeguard image boundaries
            u_center = max(0, min(u_center, depth_map.shape[1] - 1))
            v_center = max(0, min(v_center, depth_map.shape[0] - 1))
            z_depth = depth_map[v_center, u_center]
            
            # Handle invalid depth readings (NaN, Inf, or out-of-range)
            if np.isnan(z_depth) or np.isinf(z_depth) or z_depth <= 0.1:
                # Fallback: look at a small window around the center if center pixel is missing depth
                window = depth_map[max(0, v_center-2):v_center+3, max(0, u_center-2):u_center+3]
                valid_window = window[(~np.isnan(window)) & (~np.isinf(window)) & (window > 0.1)]
                z_depth = np.median(valid_window) if len(valid_window) > 0 else None
                
            # 3. Calculate 3D Centroid using pinhole camera equations
            xyz_centroid = None
            if z_depth is not None:
                x_3d = ((u_center - self.cx) * z_depth) / self.fx
                y_3d = ((v_center - self.cy) * z_depth) / self.fy
                xyz_centroid = [x_3d, y_3d, float(z_depth)]

            # 4. Update Registry State Machine
            if track_id not in self.object_registry:
                # Initialize brand new track entry
                self.object_registry[track_id] = {
                    'class': det.class_name,
                    'bbox_history': [bbox],
                    'confidence_history': [det.confidence],
                    'age': 1,
                    '3d_centroid': xyz_centroid,
                    'status': 'Activated'
                }
                self.get_logger().info(f"Registry: Tracking new {det.class_name} (ID: {track_id})")
            else:
                # Update existing track entry
                track = self.object_registry[track_id]
                track['age'] += 1
                track['3d_centroid'] = xyz_centroid if xyz_centroid is not None else track['3d_centroid']
                
                # Append history arrays and maintain size limits
                track['bbox_history'].append(bbox)
                track['confidence_history'].append(det.confidence)
                if len(track['bbox_history']) > self.max_history_len:
                    track['bbox_history'].pop(0)
                    track['confidence_history'].pop(0)
                    
                # Track confidence trends
                if len(track['confidence_history']) >= 2:
                    trend = "stable"
                    if track['confidence_history'][-1] > track['confidence_history'][-2] + 0.05:
                        trend = "increasing"
                    elif track['confidence_history'][-1] < track['confidence_history'][-2] - 0.05:
                        trend = "decreasing"
                    track['confidence_trend'] = trend

        # 5. Handle Tracking Losses (Occlusion / Out-of-frame)
        for registered_id in list(self.object_registry.keys()):
            if registered_id not in current_frame_tracks:
                # If an item was seen before but is missing this frame, check if it should be culled
                self.object_registry[registered_id]['status'] = 'Occluded'
                # Optional: If age or missing threshold exceeds limit, delete from active tracking
                # del self.object_registry[registered_id]

        # Debug printout of current tracked database size
        self.get_logger().debug(f"Active warehouse registry contains {len(self.object_registry)} items.")

def main(args=None):
    rclpy.init(args=args)
    node = FusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()