--only and --exclude are mutually exclusive (Playwright launcher)

  $ "$PYTHON" "$TESTDIR/_demo_pw_cli.py" --browser chromium --only a --exclude b 2>&1 | grep -o -E "(INVALID CLI ARGUMENTS|--only and --exclude cannot be used together)"
  INVALID CLI ARGUMENTS
  --only and --exclude cannot be used together
