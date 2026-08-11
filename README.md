# Tokamak simulation with time bridges

This repository contains an example for how to co-evolve a physical system, diagnostics
or sensors that measure the state of that system, and controllers that steer the system
based on the measured values, using MUSCLE3.

The example used here is of height control in a tokamak fusion reactor, but the concept
transfers to other situations.

The model used here does not do any kind of physics (or any realistic measurement or
control), but it has all the communication patterns a real simulation has. The plasma
model uses variable timestepping in the way an implicit Euler integrator does, while the
diagnostics and controller are each on their own regular sampling cycle.

The diagnostic receives the plasma states covering each of its sampling intervals and
computes an average height, which, after a processing delay, is sent to the controller.
The controller then picks it up at its next control cycle, calculates control input
values for the near future, and those get sent to the plasma model where they provide
feedback and hopefully keep things stable.

## Set up

Clone this repository:

```bash

git clone https://github.com/LourensVeen/tokamak_time_bridge_example
cd tokamak_time_bridge_example
```

Install it into the local `opt/` directory:

```bash
tokamak_time_bridge_example$ make
```

Next, activate the virtual environment and set the `YMMSL_PATH` environment variable
according to the instructions output by the previous step.

## Running an uncontrolled simulation

Create a new configuration file `plasma_only.ymmsl` and the following contents:

```yaml

ymmsl_version: v0.2

imports:
  - from ttb_example.reactor import implementation reactor
  - from ttb_example.programs.plasma import implementation plasma

custom_implementations:
  reactor.plasma: plasma

settings:
  muscle_remote_log_level: DEBUG
  muscle_local_log_level: DEBUG
```

This imports the tokamak reactor simulator, which provides the model's structure. It
describes connections between plasma, diagnostics, and controller, using three time
bridges to connect them pairwise so that the plasma state is sent to the diagnostics,
whose measurements are sent to the controller, whose control inputs are sent back to the
plasma model.

The `reactor` model does not have any default implementations for its six components, so
by default it does nothing. To run only the plasma model, we import that, and then plug
in into the `reactor.plasma` component. We also increase the log level to get some more
detailed output.

To run the simulation, we start it using MUSCLE3:

```bash
(venv) tokamak_time_bridge_example$ muscle_manager --start-all plasma_only.ymmsl
```

A record of the run will be written to the `muscle3_manager.log` file in the output
directory given by MUSCLE3 at the end of the run. As you can see, things are not as
stable as we'd like for them to be.

## Running with diagnostics

To observe the plasma while it's evolving, we need to add some diagnostics. Create a new
configuration file `plasma_diagnostics.ymmsl` and the following contents:

```yaml

ymmsl_version: v0.2

description: |
  This runs the plasma model, diagnostics, and the time bridge between them

imports:
  - from ttb_example.reactor import implementation reactor
  - from ttb_example.programs.plasma import implementation plasma
  - from ttb_example.programs.bridge_plasma_diagnostics import implementation bridge_plasma_diagnostics
  - from ttb_example.programs.diagnostics import implementation diagnostics

custom_implementations:
  reactor.plasma: plasma
  reactor.bridge_plasma_diagnostics: bridge_plasma_diagnostics
  reactor.diagnostics: diagnostics

settings:
  muscle_remote_log_level: DEBUG
  muscle_local_log_level: DEBUG
```

This can then be run in the same way as above, and the results inspected.

