Browser not in the platform choice list is rejected by argparse

On Linux the Selenium CLI only allows chrome and firefox; safari (macOS-only)
must therefore be rejected.

  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser safari --driver-path missing 2>&1 | grep -E "(INVALID CLI|invalid choice)"
  INVALID CLI ARGUMENTS
  *--browser: invalid choice: 'safari'* (glob)