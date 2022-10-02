# Paul Logston's `pre-commit` Hooks

A set of hooks to be used with https://pre-commit.com/.

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
