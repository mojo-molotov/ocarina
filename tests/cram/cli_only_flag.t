--only collects multiple test IDs into a tuple

  $ touch driver
  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver --only alpha beta | grep -E "^(only|exclude)="
  only=('alpha', 'beta')
  exclude=()
