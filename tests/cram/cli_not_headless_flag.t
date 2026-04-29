--not-headless flips headless to False

Headless mode is the default; the flag opts out.

  $ touch driver
  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver --not-headless
  browser=chrome
  driver_path=driver
  headless=False
  workers=5
  wait_timeout=10
  logger=terminal+file
  only=()
  exclude=()