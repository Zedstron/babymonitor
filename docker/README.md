# Docker — Experimental

This Docker support is experimental. Only use the containerized method if you know what
you are doing — this project expects direct access to hardware and low-level services.

Key warnings
- **Experimental:** This setup is experimental and may be unstable or crash.
- **Advanced only:** Use Docker only if you understand device passthrough, host
	networking, and privileged containers.
- **Hardware compatibility:** Docker Engine is best compatible with Raspberry Pi 4 or 5
	on supported OS images. Other platforms or older Pi models may not work reliably.

Required host hardware and services
- Camera (video device accessible to the process)
- Audio (ALSA/Pulse access / sound devices)
- GPIO bus access
- Infrared service (e.g., `lirc` or equivalent kernel userspace support)
- Host network access for WireGuard (WireGuard requires host-level networking)

Why containers are fragile here
This application integrates tightly with multiple host subsystems (camera, audio, GPIO,
infrared, WireGuard). Running inside a container requires exposing those devices and
services to the container (device mounts, privileged mode, host networking). Even with
those settings, behavior can be less stable than a direct host install and debugging
will be harder.

Recommended installation
- Preferred: Install on the host OS (no containerization) or run the included
	`setup.sh` script to configure the system for all required hardware and services.
	See [setup.sh](setup.sh) for the recommended host install path.
- If you must use Docker: this is an advanced, unsupported workflow. You will need to
	expose devices and run the container with host networking and sufficiently
	permissive privileges. Expect additional debugging and instability.

Support and issues
If you experience problems with a containerized setup, reproduce the issue on a
host install (using `setup.sh`) before filing bugs. Host installs are the baseline
configuration and are far easier to debug.

Contact
For questions or to report hardware compatibility notes, open an issue in this
repository and include platform details (Pi model, OS image, kernel version).