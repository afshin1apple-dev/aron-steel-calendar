2026-08-21T08:22:09.6679881Z ##[group]Run python market.py
2026-08-21T08:22:09.6680316Z [36;1mpython market.py[0m
2026-08-21T08:22:09.6723256Z shell: /usr/bin/bash -e {0}
2026-08-21T08:22:09.6723620Z env:
2026-08-21T08:22:09.6723998Z   pythonLocation: /opt/hostedtoolcache/Python/3.12.14/x64
2026-08-21T08:22:09.6724521Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.14/x64/lib/pkgconfig
2026-08-21T08:22:09.6725029Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.14/x64
2026-08-21T08:22:09.6725521Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.14/x64
2026-08-21T08:22:09.6725982Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.14/x64
2026-08-21T08:22:09.6726446Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.14/x64/lib
2026-08-21T08:22:09.6727202Z   BOT_TOKEN: ***
2026-08-21T08:22:09.6727515Z   CHANNEL_ID: ***
2026-08-21T08:22:09.6727962Z   PEXELS_API_KEY: ***
2026-08-21T08:22:09.6728290Z ##[endgroup]
2026-08-21T08:22:13.0733382Z Traceback (most recent call last):
2026-08-21T08:22:13.0740590Z   File "/home/runner/work/aron-steel-calendar/aron-steel-calendar/market.py", line 183, in <module>
2026-08-21T08:22:13.0741763Z     tether, tether_change = get_tether()
2026-08-21T08:22:13.0742202Z                             ^^^^^^^^^^^^
2026-08-21T08:22:13.0743263Z   File "/home/runner/work/aron-steel-calendar/aron-steel-calendar/market.py", line 111, in get_tether
2026-08-21T08:22:13.0744149Z     raise RuntimeError("Tether IRR price not found")
2026-08-21T08:22:13.0744643Z RuntimeError: Tether IRR price not found
2026-08-21T08:22:13.1175640Z ##[error]Process completed with exit code 1.
