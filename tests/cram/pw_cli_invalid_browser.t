Only Playwright engines (chromium/firefox/webkit) are accepted

A Selenium-style browser name like chrome must be rejected by argparse.

  $ "$PYTHON" "$TESTDIR/_demo_pw_cli.py" --browser chrome 2>&1 | grep -E "(INVALID CLI|invalid choice)"
  INVALID CLI ARGUMENTS
  *--browser: invalid choice: 'chrome'* (glob)
