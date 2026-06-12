#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "sensor_msgs/msg/camera_info.hpp"
#include "cv_bridge/cv_bridge.h"
#include <opencv2/opencv.hpp>

// We are creating a class that inherits from standard ROS 2 Nodes
class ZEDInputNode : public rclcpp::Node {
public:
    // 1. CONSTRUCTOR: This runs once when the node starts up [cite: 100]
    ZEDInputNode() : Node("zed_input_node") {
        
        // Create "Publishers" (megaphones) to broadcast the images [cite: 102]
        rgb_pub_ = this->create_publisher<sensor_msgs::msg::Image>("/zed/rgb/image", 10);
        depth_pub_ = this->create_publisher<sensor_msgs::msg::Image>("/zed/depth/image", 10);
        info_pub_ = this->create_publisher<sensor_msgs::msg::CameraInfo>("/zed/camera_info", 10);

        // Create a Timer that triggers the "on_timer" function 30 times a second (30 Hz) 
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(33), // 33ms = ~30 Hz
            std::bind(&ZEDInputNode::on_timer, this));
            
        RCLCPP_INFO(this->get_logger(), "ZED Input Node has started up successfully!");
    }

private:
    // 2. THE LOOP: This function runs automatically every 33 milliseconds [cite: 101]
    void on_timer() {
        // NOTE: Later, we will link the actual ZED SDK hardware code here.
        // For now, we are creating an empty image to test that our ROS 2 connections work.
        
        cv::Mat empty_rgb_frame = cv::Mat::zeros(480, 640, CV_8UC3); // 640x480 resolution [cite: 109]
        
        // Convert the OpenCV image into a ROS 2 format using cv_bridge [cite: 101]
        std_msgs::msg::Header header;
        header.stamp = this->get_clock()->now();
        header.frame_id = "zed_camera_center";
        
        sensor_msgs::msg::Image::SharedPtr rgb_msg = cv_bridge::CvImage(header, "bgr8", empty_rgb_frame).toImageMsg();
        
        // Publish the message out to the network [cite: 101]
        rgb_pub_->publish(*rgb_msg);
    }

    // Variables to hold our publishers and timer
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr rgb_pub_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr depth_pub_;
    rclcpp::Publisher<sensor_msgs::msg::CameraInfo>::SharedPtr info_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

// 3. MAIN FUNCTION: The starting point of the whole C++ program
int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ZEDInputNode>()); // Keep the node running forever
    rclcpp::shutdown();
    return 0;
}