from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Start the ZED Camera Node
        Node(
            package='zed_input_node',
            executable='zed_input_node',
            name='zed_input_node',
            parameters=[{'use_sim_time': True}] # Force simulator clock
        ),
        
        # 2. Start the ORB-SLAM3 Brain
        Node(
            package='orb_slam3_node',
            executable='orb_slam_node',
            name='orb_slam3_node',
            parameters=[{'use_sim_time': True}] # Force simulator clock
        ),
        
        # 3. Start the YOLOv8 AI
        Node(
            package='yolo_detection_node',
            executable='yolo_node',
            name='yolo_detection_node',
            parameters=[{'use_sim_time': True}] # Force simulator clock
        )
    ])