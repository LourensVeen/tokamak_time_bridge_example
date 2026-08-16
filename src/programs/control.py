#!/usr/bin/env python3

"""Controller model

This simulates the vertical control component. It takes measurements from the height
diagnostic, compares those the the plasma height set point, and produces a control
output that pushes the plasma towards the set point. The controller has its own
sense-think-act loop with a configurable period/frequency.

Ports:
    clock_out (diagnostics O_I): Sends an empty message for synchronisation purposes.
    height_in (diagnostics S): Receives the measured height.
    control_out (control O_I): Sends the measured height, relative to the sensor
        position.

Settings:
    d_think: Amount of time it takes to compute a control output.
    t_begin: Time at which the controller starts controlling.
    dt: Time between control cycles.
    t_end: Time at which the controller stops controlling.
"""

import logging
from libmuscle import Instance, InstanceFlags, Message
from ymmsl import Operator


def main() -> None:
    logger = logging.getLogger()

    # Timeline diagnostics: clock_out, height_in
    # Timeline control: control_out
    instance = Instance(
        {Operator.S: ["height_in"], Operator.O_I: ["clock_out", "control_out"]},
        InstanceFlags.SKIP_MMSF_SEQUENCE_CHECKS,
    )

    while instance.reuse_instance():
        # F_INIT
        gain = instance.get_setting("gain", "float", default=10.0)
        set_point = instance.get_setting("set_point", "float", default=0.0)
        d_think = instance.get_setting("d_think", "float", default=1e-4)

        t_begin = instance.get_setting("t_begin", "float", default=0.0)
        dt = instance.get_setting("dt", "float", default=0.01)
        t_end = instance.get_setting("t_end", "float", default=1.0)

        t_cur = t_begin
        t_control = t_begin
        t_next_control = t_cur + dt + d_think
        prev_control = 0.0
        control = 0.0
        data = [
            [t_begin, prev_control],
            [t_next_control, control],
        ]
        while t_cur < t_end:
            # O_I
            t_next = t_cur + dt if t_cur + dt < t_end else None
            instance.send("clock_out", Message(t_cur, t_next, None))

            logger.debug(f"sending control data: {data}")
            instance.send("control_out", Message(t_control, t_next_control, data))

            # S
            height_msg = instance.receive("height_in")

            logger.info(f"Received height at {height_msg.timestamp}: {height_msg.data}")
            i = len(height_msg.data)
            while i > 0 and t_cur < height_msg.data[i - i][0]:
                i -= 1
            latest_height = height_msg.data[i - 1][1]

            prev_control = control
            control = -gain * (latest_height - set_point)

            t_cur += dt

            # create curve from current actuator state to next
            t_control = t_cur + d_think
            t_next_control = t_cur + dt + d_think if t_cur + dt < t_end else None

            data = [[t_control, prev_control], [t_cur + dt + d_think, control]]
            logger.info(f"t_control: {t_control}, t_next_control: {t_next_control}")


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    main()
