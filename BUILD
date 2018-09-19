load(
    "//rules/core/Python/build_defs.py",
)

py_library(
  name = "pyremote_core",
  srcs = [
    "netspec.py",
    "serialize.py",
  ],
)

py_library(
  name = "pyremote_client",
  srcs = [
    "client.py",
  ],
  deps = [
    ":pyremote_core",
  ],
)

py_library(
  name = "server",
  srcs = [
    "server.py",
  ],
  deps = [
    ":pyremote_core",
  ],
)