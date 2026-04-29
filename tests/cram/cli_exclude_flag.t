--exclude collects multiple test IDs into a tuple

  $ touch driver
  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --browser chrome --driver-path driver --exclude gamma | grep -E "^(only|exclude)="
  only=()
  exclude=('gamma',)
