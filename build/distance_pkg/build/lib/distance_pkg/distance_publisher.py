import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import RPi.GPIO as GPIO

TRIG = 23
ECHO = 24

class DistancePublisher(Node):
    def __init__(self):
        super().__init__('distance_publisher')

        # create the publisher: message type, topic name, queue size
        self.publisher_ = self.create_publisher(Float32, 'distance', 10)

        # set up the sensor pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)
        GPIO.output(TRIG, False)
        self.get_logger().info('Waiting for sensor to settle')
        time.sleep(2)

        # call timer_callback every 2 seconds
        self.timer = self.create_timer(2.0, self.timer_callback)
        self.get_logger().info("Publishing distance on /distance every 2 seconds")

    def measure(self, timeout=0.04):
        """Take one reading in cm or return none"""
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        start = time.time()
        pulse_start = start
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if pulse_start - start > timeout:
                return None

        pulse_end = pulse_start
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if pulse_end - pulse_start > timeout:
                return None

        return round((pulse_end - pulse_start) * 17150, 2)

    def timer_callback(self):
        distance = self.measure()
        if distance is None:
            self.get_logger().warn('No reading from sensor')
            return

        msg = Float32()
        msg.data = float(distance)
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published distance: {distance} cm')

    def destroy_node(self):
        GPIO.cleanup()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DistancePublisher()
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