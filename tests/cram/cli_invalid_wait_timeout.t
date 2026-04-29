--wait-timeout over the documented max is rejected with a clear message

  $ touch driver
  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver --wait-timeout 9999 2>&1 | grep -oE "wait-timeout maximum is: 60"
  wait-timeout maximum is: 60

Zero triggers the is_not_zero check.

  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver --wait-timeout 0 2>&1 | grep -oE "wait-timeout should not be zero"
  wait-timeout should not be zero

Negative triggers the is_positive check.

  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver --wait-timeout -1 2>&1 | grep -oE "wait-timeout should be a positive value"
  wait-timeout should be a positive value