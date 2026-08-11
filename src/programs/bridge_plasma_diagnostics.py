#!/usr/bin/env python3

"""Time bridge connecting plasma to diagnostics

This time bridge receives the plasma state from the plasma model, at whichever time
points that model has, and receives a clock signal from the diagnostics indicating when
it wants to get data. It then sends the plasma state at that point in time to the
diagnostics. In this example we simply send the most recent state, but it's easily
modified to interpolate, integrate, or average as needed.

Ports:
    plasma_state_in (plasma S): Receives plasma state from plasma model
    diag_clock_in (diagnostics S): Timing input from the diagnostics model
    plasma_state_out (diagnostics O_I): Plasma state for the diagnostics model

"""

import logging
from libmuscle import Instance, InstanceFlags, Message
from ymmsl import Operator


def main() -> None:
    logger = logging.getLogger()

    # Timeline plasma: plasma_state_in
    # Timeline diagnostics: diag_clock_in, plasma_state_out
    instance = Instance(
        {
            Operator.S: ["plasma_state_in", "diag_clock_in"],
            Operator.O_I: ["plasma_state_out"],
        },
        InstanceFlags.SKIP_MMSF_SEQUENCE_CHECKS,
    )

    while instance.reuse_instance():
        plasma_data = []
        diag_next: float | None = 0.0
        plasma_cur: float = float("-inf")
        plasma_next: float | None = 0.0
        while diag_next is not None:
            # Receive the next diagnostics integration window
            diag_clock_msg = instance.receive("diag_clock_in")
            diag_cur = diag_clock_msg.timestamp
            diag_next = diag_clock_msg.next_timestamp
            logger.debug(f"Got diag_cur = {diag_cur}, diag_next = {diag_next}")

            # Receive any additional plasma data we need to cover it
            while plasma_next is not None and (
                diag_next is None or plasma_cur < diag_next
            ):
                plasma_state_msg = instance.receive("plasma_state_in")
                plasma_cur = plasma_state_msg.timestamp
                plasma_next = plasma_state_msg.next_timestamp
                plasma_data.append([plasma_cur, plasma_state_msg.data])
                logger.info(
                    f"Got plasma_cur = {plasma_cur}, plasma_next = {plasma_next}"
                )

            # Remove all plasma data before the last value prior to diag_cur
            logger.debug(f"removing before {diag_cur}")
            i = 0
            while i < len(plasma_data) and plasma_data[i][0] <= diag_cur:
                i += 1
            plasma_data = plasma_data[max(0, i - 1):]
            logger.debug(f"{plasma_next} {diag_next} plasma_data now {plasma_data}")

            # Send plasma data for the current window
            logger.info(
                f"Sending {len(plasma_data)} plasma states for window"
                f" {diag_cur} to {diag_next}"
            )
            instance.send("plasma_state_out", Message(diag_cur, diag_next, plasma_data))


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    main()
