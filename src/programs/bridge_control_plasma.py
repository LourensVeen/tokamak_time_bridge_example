#!/usr/bin/env python3

"""Time bridge connecting control to plasma

This time bridge receives the control inputs from the control system, at whichever time
points it produces them, and receives a clock signal from the plasma model indicating
when its next time step is. The bridge then sends control inputs covering that period to
the plasma model in the form of a control points for a piecewise linear function. The
plasma model then interpolates between those to get a control value for whichever next
time point it attempts to step to.

Ports:
    control_in (control S): Receives control input from control
    plasma_clock_in (plasma S): Timing input from the plasma model
    control_out (plasma O_I): Control input for the plasma model

"""

import logging
from libmuscle import Instance, InstanceFlags, Message
from ymmsl import Operator


def main() -> None:
    logger = logging.getLogger()

    # Timeline plasma: control_in
    # Timeline plasma: plasma_clock_in, control_out
    instance = Instance(
        {
            Operator.S: ["control_in", "plasma_clock_in"],
            Operator.O_I: ["control_out"],
        },
        InstanceFlags.SKIP_MMSF_SEQUENCE_CHECKS,
    )

    while instance.reuse_instance():
        t_begin = instance.get_setting("t_begin", "float", default=0.0)

        plasma_next: float | None = 0.0
        control_cur: float = t_begin
        control_next: float | None = 0.0
        control_data = []
        while plasma_next is not None:
            # Receive the next plasma timestep
            plasma_clock_msg = instance.receive("plasma_clock_in")
            plasma_cur = plasma_clock_msg.timestamp
            plasma_next = plasma_clock_msg.next_timestamp
            logger.debug(f"Got plasma_cur = {plasma_cur}, plasma_next = {plasma_next}")

            # Receive any additional control data we need to cover it
            while (
                control_next is not None  # more control data available
                and (
                    plasma_next is None  # plasma window reaches to end of sim
                    or control_next < plasma_next
                )
            ):
                control_msg = instance.receive("control_in")
                control_cur = control_msg.timestamp
                control_next = control_msg.next_timestamp
                control_data.extend(control_msg.data)
                logger.debug(
                    f"Got control_cur = {control_cur}, control_next = {control_next}"
                )

            # Remove all control data before the last value prior to plasma_cur
            i = 0
            while i < len(control_data) and control_data[i][0] <= plasma_cur:
                i += 1
            control_data = control_data[max(0, i - 1) :]

            # Send control data for the current window
            logger.info(
                f"Sending {len(control_data)} control states for window"
                f" {plasma_cur} to {plasma_next}"
            )
            instance.send("control_out", Message(plasma_cur, plasma_next, control_data))


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    main()
