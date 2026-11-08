## Task

I need a job queue in Python backed by SQLite: enqueue jobs from code, run them in several worker processes, retry failures with backoff, and survive the machine being killed mid-job without losing or double-running work. Add a small CLI to see what is pending, running, failed.

## Follow-up (send after the first turn is done and committed)

Add scheduled jobs (run at a time, and cron-style repeating), and job dependencies where a job only starts after the ones it depends on succeed.
