# Paul Logston's `pre-commit` Hooks

A set of hooks to be used with https://pre-commit.com/.

### Install

Add to your `.pre-commit-config.yaml`...

```
-   repo: https://github.com/logston/my-pre-commit-hooks
    rev: v0.1.0 <<< udpate this to newest git tag
    hooks:
    -   id: jhu-check-closing-block-comments
```

### Development
```
poetry install
```

In the repo to test the hook on:

```
pre-commit try-repo ../my-pre-commit-hooks/ <hook id> --verbose --all-files
```

### Testing
```
poetry run pytest
```
