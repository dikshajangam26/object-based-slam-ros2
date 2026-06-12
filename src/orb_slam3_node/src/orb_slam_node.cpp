#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "cv_bridge/cv_bridge.h"

// We are creating a node to wrap the ORB-SLAM3 library
class ORBSLAMNode : public rclcpp::Node {
public:
    ORBSLAMNode() : Node("orb_slam3_node") {
        
        // 1. Subscribe to the ZED camera images
        image_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
            "/zed/rgb/image", 10, std::bind(&ORBSLAMNode::image_callback, this, std::placeholders::_1));

        // 2. Create publishers for the tracked pose (location)
        pose_pub_ = this->create_publisher<geometry_msgs::msg::PoseStamped>("/slam/pose", 30);
        
        RCLCPP_INFO(this->get_logger(), "ORB-SLAM3 Node Initialized! Waiting for images...");
        
        // NOTE: In a full production file, this is where we would load the ORBvoc.txt vocabulary 
        // and camera calibration files to initialize the actual ORB_SLAM3::System object.
    }

private:
    void image_callback(const sensor_msgs::msg::Image::SharedPtr msg) {
        // Convert ROS image to an OpenCV image so ORB-SLAM can read it
        cv_bridge::CvImagePtr cv_ptr;
        try {
            cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
        } catch (cv_bridge::Exception& e) {
            RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
            return;
        }

        // NOTE: Here we would pass cv_ptr->image into the ORB-SLAM3 tracking engine.
        // For now, we will just publish a dummy pose to verify the network is connected.

        geometry_msgs::msg::PoseStamped pose_msg;
        pose_msg.header.stamp = this->get_clock()->now();
        pose_msg.header.frame_id = "world"; // The fixed origin point
        
        // Setting a fake position (x, y, z) just to test our publisher
        pose_msg.pose.position.x = 0.0;
        pose_msg.pose.position.y = 0.0;
        pose_msg.pose.position.z = 0.0;

        pose_pub_->publish(pose_msg);
    }

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ORBSLAMNode>());
    rclcpp::shutdown();
    return 0;
}