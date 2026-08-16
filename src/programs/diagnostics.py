#!/usr/bin/env python3

"""Diagnostics model

This simulates a simple diagnostic that receives the plasma state and measures the
height of the plasma relative to the sensor. It has its own measurement loop with a
configurable measurement period/frequency, and it communicates with the outside world on
two timelines: one for the plasma and one for the resulting measurements. On the plasma
side, it provides a "clock_out" port on which an empty message is sent for every time
point at which it wants to receive the plasma state.

Ports:
    clock_out (O_I): Sends an empty message for synchronisation purposes.
    height_out (O_I): Sends the measured height.
    plasma_state_in (S): Receives the plasma state.

Settings:
    sensor_position: Position of the sensor relative to center of vessel.
    d_meas: Amount of time a measurement takes to complete.
    t_begin: Time at which the diagnostic starts measuring.
    dt: Time between start of successive measurements.
    t_end: Time at which the diagnostic stops measuring.
"""

import logging
import random
from libmuscle import Instance, Message
from ymmsl import Operator


def main() -> None:
    logger = logging.getLogger()

    instance = Instance(
        {Operator.S: ["plasma_state_in"], Operator.O_I: ["clock_out", "height_out"]}
    )

    while instance.reuse_instance():
        # F_INIT
        t_begin = instance.get_setting("t_begin", "float", default=0.0)
        dt = instance.get_setting("dt", "float", default=0.01)
        t_end = instance.get_setting("t_end", "float", default=1.0)

        d_meas = instance.get_setting("d_meas", "float", default=1e-4)
        stddev = instance.get_setting("stddev", "float", default=0.2)

        t_cur = t_begin
        data = [t_cur + 0.5 * dt, 0.0]

        while t_cur < t_end:
            # O_I
            t_next = t_cur + dt if t_cur + dt < t_end else None
            instance.send("clock_out", Message(t_cur, t_next, None))
            t_meas = t_cur + dt + d_meas
            t_meas_next = t_meas + dt if t_cur + dt < t_end else None
            instance.send("height_out", Message(t_meas, t_meas_next, data))

            # S
            plasma_state_msg = instance.receive("plasma_state_in")

            n = len(plasma_state_msg.data)
            real_height = sum([d[1] for d in plasma_state_msg.data]) / n

            # measurement O_I
            measurement = real_height + random.normalvariate(0.0, stddev)
            data = [t_cur + 0.5 * dt, measurement]
            logger.info(f"t_cur: {t_cur}, t_meas: {t_meas}, measurement: {measurement}")

            t_cur += dt


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    main()
