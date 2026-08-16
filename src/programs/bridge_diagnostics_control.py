#!/usr/bin/env python3

"""Time bridge connecting diagnostics to controller

This time bridge receives measurements from the diagnostics, at whichever time
points it provides them, and receives a clock signal from the controller indicating when
it wants to get data. It then sends the latest measurement at that point in time to the
controller.

Ports:
    height_in (diagnostics S): Receives plasma height measurement from diagnostics
    control_clock_in (control S): Timing input from the controller model
    height_out (control O_I): Height measurement for the diagnostics model

"""

import logging
from libmuscle import Instance, InstanceFlags, Message
from ymmsl import Operator


def main() -> None:
    logger = logging.getLogger()

    # Timeline diagnostics: height_in
    # Timeline control: control_clock_in, height_out
    instance = Instance(
        {
            Operator.S: ["height_in", "control_clock_in"],
            Operator.O_I: ["height_out"],
        },
        InstanceFlags.SKIP_MMSF_SEQUENCE_CHECKS,
    )

    while instance.reuse_instance():
        diag_data = []
        control_next: float | None = 0.0
        diag_cur: float = float("-inf")
        diag_next: float | None = 0.0
        while control_next is not None:
            # Receive the next control decision point
            control_clock_msg = instance.receive("control_clock_in")
            control_cur = control_clock_msg.timestamp
            control_next = control_clock_msg.next_timestamp
            logger.debug(
                f"Got control_cur = {control_cur}, control_next = {control_next}"
            )

            # Receive any additional plasma data we need to cover it
            while diag_next is not None and (
                control_next is None or diag_cur < control_next
            ):
                height_msg = instance.receive("height_in")
                diag_cur = height_msg.timestamp
                diag_next = height_msg.next_timestamp
                diag_data.append(height_msg.data)
                logger.debug(f"Got diag_cur = {diag_cur}, diag_next = {diag_next}")

            # Remove all measurements before the last value prior to control_cur
            i = 0
            while i < len(diag_data) and diag_data[i][0] <= control_cur:
                i += 1
            diag_data = diag_data[max(0, i - 1) :]

            # Send measurements for the current window
            logger.info(
                f"Sending {len(diag_data)} heights for window"
                f" {control_cur} to {control_next}"
            )
            instance.send("height_out", Message(control_cur, control_next, diag_data))


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    main()
