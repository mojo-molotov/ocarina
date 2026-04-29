--only and --exclude are mutually exclusive

  $ touch driver
  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver --only a --exclude b 2>&1 | grep -o -E "(INVALID CLI ARGUMENTS|--only and --exclude cannot be used together)"
  INVALID CLI ARGUMENTS
  --only and --exclude cannot be used together
