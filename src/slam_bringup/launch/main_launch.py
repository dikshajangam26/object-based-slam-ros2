from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. ZED Camera Node
        Node(
            package='zed_input_node',
            executable='zed_input_node',
            name='zed_input_node',
            parameters=[{'use_sim_time': True}]
        ),
        
        # 2. ORB-SLAM3 Core
        Node(
            package='orb_slam3_node',
            executable='orb_slam_node',
            name='orb_slam3_node',
            parameters=[{'use_sim_time': True}]
        ),
        
        # 3. YOLOv8 AI Tracking Node (TensorRT Optimized)
        Node(
            package='yolo_detection_node',
            executable='yolo_node',
            name='yolo_detection_node',
            parameters=[{'use_sim_time': True}]
        ),
        
        # 4. Sensor Fusion & Object State Registry Node
        Node(
            package='fusion_node',
            executable='fusion_node',
            name='fusion_node',
            parameters=[{'use_sim_time': True}],
            output='screen' # Ensures log tracking prints directly to your terminal
        )
    ])