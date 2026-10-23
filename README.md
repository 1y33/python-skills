# python-skills

Two agent skills for Python work:

- **python-dev**: writing, reviewing, and setting up Python. Typed contracts, understandable execution, usable APIs, deliberate extension points, reliable operation. Topic references (async, FastAPI, pipelines, security, observability, …) load only when the task touches them.
- **python-refactor**: behavior-preserving cleanup. Scoped audit, characterization tests, small verified steps toward the python-dev patterns.

## Install

**Claude Code**

```sh
claude plugin marketplace add 1y33/python-skills
claude plugin install python-skills@python-skills
```

**Pi**

```sh
pi install git:github.com/1y33/python-skills
```

**Anything else** that reads `SKILL.md` folders: copy or symlink `skills/python-dev` and `skills/python-refactor` into your agent's skills directory.

## Test

```sh
bash tests/skills.sh
```

## License

MIT
