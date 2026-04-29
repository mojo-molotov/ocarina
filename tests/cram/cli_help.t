CLI --help lists every declared flag

Pipe through grep to stay resilient to unrelated wording changes in argparse's
help output. Sorted unique output → alphabetical by first-differing character.

  $ "$PYTHON" "$TESTDIR/_demo_cli.py" --help 2>&1 | grep -o -- '--\(driver-path\|profile-path\|browser\|not-headless\|workers\|logger\|wait-timeout\|dont-force-delete-tmp-dirs\|only\|exclude\)' | sort -u
  --browser
  --dont-force-delete-tmp-dirs
  --driver-path
  --exclude
  --logger
  --not-headless
  --only
  --profile-path
  --wait-timeout
  --workers