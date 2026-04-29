--driver-path pointing to a non-existent file is rejected

The framework validates that the driver path resolves to an actual file on
disk (Safari aside, which uses safaridriver natively).

  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path /tmp/does-not-exist-xxxxx 2>&1 | grep -oE -- '--driver-path should be a path to a file' | head -1
  --driver-path should be a path to a file

With no --driver-path at all the same validation fires (default is empty string).

  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome 2>&1 | grep -oE -- '--driver-path should be a path to a file' | head -1
  --driver-path should be a path to a file