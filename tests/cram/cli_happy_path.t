Valid args produce a deterministic parsed config

  $ touch driver
  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser firefox --driver-path driver --workers 3 --wait-timeout 20 --logger terminal
  browser=firefox
  driver_path=driver
  headless=True
  workers=3
  wait_timeout=20
  logger=terminal
  only=()
  exclude=()