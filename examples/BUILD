load(
    "//rules/core/Python/build_defs.py",
)

py_binary(
  name = "bulb",
  srcs = [
    "bulb.py",
  ],
  deps = [
    "//pyremote:pyremote_client",
  ],
)

py_binary(
  name = "control_panel",
  srcs = [
    "control_panel.py",
  ],
  deps = [
    "//pyremote:pyremote_client",
  ],
)

py_binary(
  name = "server",
  srcs = [
    "server.py",
  ],
  deps = [
    "//pyremote:server",
  ],
)