## Task

Write a small build tool in Python, like a simpler make: targets in a TOML file with commands, inputs, outputs and dependencies. It rebuilds only what changed (content, not timestamps), runs independent targets in parallel, and stops cleanly on the first failure.

## Follow-up (send after the first turn is done and committed)

Add a remote cache so a target built on one machine can be downloaded on another instead of rebuilt (a local directory standing in for the remote is fine), and a `--watch` mode.
