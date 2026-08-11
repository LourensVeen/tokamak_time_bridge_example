"""Controller model

This simulates a controller for vertical control. It has a control loop in which it
receives measurements from a diagnostic (sensor), decides what to do, computes an
actuator response, and outputs that response.

Ports:
    clock_out (diagnostic O_I): Sends an empty message for synchronisation purposes.
    height_in (diagnostic S): Receives the most recent height measurement.
    control_out (actuator O_I): Sends actuator value curve for the near future.

Settings:
    sensor_position: Position of the sensor relative to center of vessel.
    set_point: Target height of plasma relative to center of vessel.

"""
