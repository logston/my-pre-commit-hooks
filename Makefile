publish:
	git tag `grep version pyproject.toml | awk '{split($0, a, "\""); print(a[2])}'`
	git push origin HEAD
	git push origin --tags
