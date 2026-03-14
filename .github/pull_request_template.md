## Summary

Describe the change and why it is needed.

## Validation

- [ ] `python3 -m py_compile skb/*.py skb/chunkers/*.py tests/*.py scripts/*.py`
- [ ] `uv run --with pytest --with build pytest -q`
- [ ] Docs updated if user-facing behavior changed
- [ ] Install or release flow tested if packaging changed

## Notes

Call out any follow-up work, tradeoffs, or known limitations.
