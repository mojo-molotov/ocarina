Unset flags fall back to declared defaults

  $ touch driver
  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver
  browser=chrome
  driver_path=driver
  headless=True
  workers=5
  wait_timeout=10
  logger=terminal+file
  only=()
  exclude=()