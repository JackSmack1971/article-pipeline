.PHONY: verify

# Canonical verification command referenced by CLAUDE.md. Thin wrapper: the
# real logic lives in scripts/verify.sh so it can also be run directly on
# platforms without `make`.
verify:
	bash scripts/verify.sh
