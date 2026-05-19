.PHONY: bootstrap test package clean install-claude install-openclaw install-qwenpaw release

bootstrap:
	bash scripts/bootstrap.sh

test:
	bash scripts/smoke_test.sh

package:
	python3 scripts/package_skill.py

install-claude:
	bash scripts/install_skill.sh --platform claude --force

install-openclaw:
	bash scripts/install_skill.sh --platform openclaw --force

install-qwenpaw:
	bash scripts/install_skill.sh --platform qwenpaw --force

release:
	@[ -n "$$REPO" ] || (echo "REPO is required, e.g. REPO=T1anhu4/Crush.skill"; exit 1)
	@[ -n "$$TAG" ] || (echo "TAG is required, e.g. TAG=v0.1.0"; exit 1)
	@[ -n "$$GITHUB_TOKEN" ] || (echo "GITHUB_TOKEN is required"; exit 1)
	bash scripts/publish_release.sh --repo "$$REPO" --tag "$$TAG"

clean:
	rm -rf .venv
	rm -f Crush邂逅.skill/data/*.sqlite3
	rm -f Crush邂逅.skill/dist/*.zip
