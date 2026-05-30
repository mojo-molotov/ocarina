CLI --help lists every declared flag (Playwright launcher)

Pipe through grep to stay resilient to unrelated wording changes in argparse's
help output. Note there is no --driver-path: Playwright ships its own browsers.

  $ "$PYTHON" "$TESTDIR/_demo_pw_cli.py" --help 2>&1 | grep -o -- '--\(profile-path\|browser\|not-headless\|workers\|logger\|wait-timeout\|video-dir\|trace-dir\|only\|exclude\)' | sort -u
  --browser
  --exclude
  --logger
  --not-headless
  --only
  --profile-path
  --trace-dir
  --video-dir
  --wait-timeout
  --workers
