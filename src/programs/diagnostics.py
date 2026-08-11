#!/usr/bin/env python3

"""Diagnostics model

This simulates a simple diagnostic that receives the plasma state and measures the
height of the plasma relative to the sensor. It has its own measurement loop with a
configurable measurement period/frequency, and it communicates with the outside world on
two timelines: one for the plasma and one for the resulting measurements. On the plasma
side, it provides a "clock_out" port on which an empty message is sent for every time
point at which it wants to receive the plasma state.

Ports:
    clock_out (plasma O_I): Sends an empty message for synchronisation purposes.
    plasma_state_in (plasma S): Receives the plasma state.
    height_out (measurement O_I): Sends the measured height, relative to the sensor
        position.

Settings:
    sensor_position: Position of the sensor relative to center of vessel.
    d_meas: Amount of time a measurement takes to complete.
    t_begin: Time at which the diagnostic starts measuring.
    dt: Time between start of successive measurements.
    t_end: Time at which the diagnostic stops measuring.
"""

import logging
from libmuscle import Instance, Message
from ymmsl import Operator


def main() -> None:
    logger = logging.getLogger()

    # Timeline plasma: clock_out, plasma_state_in
    # Timeline measurement: height_out
    instance = Instance(
        {Operator.S: ["plasma_state_in"], Operator.O_I: ["clock_out", "height_out"]}
    )

    while instance.reuse_instance():
        # F_INIT
        sensor_position = instance.get_setting("sensor_position", "float", default=0.0)
        d_meas = instance.get_setting("d_meas", "float", default=1e-4)

        t_begin = instance.get_setting("t_begin", "float", default=0.0)
        dt = instance.get_setting("dt", "float", default=0.001)
        t_end = instance.get_setting("t_end", "float", default=1.0)

        t_cur = t_begin
        while t_cur < t_end:
            # plasma O_I
            t_next = t_cur + dt if t_cur + dt < t_end else None
            instance.send("clock_out", Message(t_cur, t_next, None))

            # plasma S
            plasma_state_msg = instance.receive("plasma_state_in")

            logger.info(f"Received plasma state {plasma_state_msg.data}")
            n = len(plasma_state_msg.data)
            real_height = sum([d[1] for d in plasma_state_msg.data]) / n

            # measurement O_I
            measurement = real_height - sensor_position
            t_meas = t_cur + dt + d_meas
            data = t_meas, measurement
            instance.send("height_out", Message(t_meas, t_meas + dt, data))
            logger.info(f"t_cur: {t_cur}, t_meas: {t_meas}, measurement: {measurement}")

            t_cur += dt


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    main()
