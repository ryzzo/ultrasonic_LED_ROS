import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class DistanceSubscriber(Node):
    def __init__(self):
        super().__init__('distance_subscriber')
        self.subscription = self.create_subscription(
            Float32, 'distance', self.listener_callback, 10
        )

    def listener_callback(self, msg):
        self.get_logger().info(f"Recieved distance: {msg.data:.2f} cm")


def main(args=None):
    rclpy.init(args=args)
    node = DistanceSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()