import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import RPi.GPIO as GPIO

LED_PIN = 18

class LedController(Node):
    def __init__(self):
        super().__init__('led_controller')

        # parameters
        self.declare_parameter('threshold_cm', 5.0)
        self.declare_parameter('timeout_s', 5.0)

        # Set up the LED pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(LED_PIN, GPIO.OUT)
        GPIO.output(LED_PIN, GPIO.LOW)
        self.led_on = False

        # Remember when distance was last read
        self.last_msg_time = self.get_clock().now()

        # Listen to /distance
        self.subscription = self.create_subscription(
            Float32, 'distance', self.distance_callback, 10
        )

        # safety check once per second
        self.watchdog = self.create_timer(1.0, self.watchdog_callback)

        self.get_logger().info("LED controller ready, listening on /distance")

    def set_led(self, on):
        """Change the LED only when its state actually changes"""
        if on != self.led_on:
            GPIO.output(LED_PIN, GPIO.HIGH if on else GPIO.LOW)
            self.led_on = on
            self.get_logger().info('LED ON' if on else 'LED OFF')

    def distance_callback(self, msg):
        self.last_msg_time = self.get_clock().now()
        threshold = self.get_parameter('threshold_cm').value
        self.set_led(msg.data < threshold)

    def watchdog_callback(self):
        timeout = self.get_parameter('timeout_s').value
        elapsed = (self.get_clock().now() - self.last_msg_time).nanoseconds / 1e9
        if self.led_on and elapsed > timeout:
            self.get_logger().warn(f"No distance for {elapsed:.1f}s. turning LED off")
            self.set_led(False)

    def destroy_node(self):
        GPIO.output(LED_PIN, GPIO.LOW)
        GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = LedController()
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

