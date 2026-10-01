VENV   := .venv
PY     := $(VENV)/bin/python
TF_DIR := infra/terraform

.PHONY: venv test lint fmt tf-fmt tf-validate plan apply destroy invoke check

venv:
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -r requirements-dev.txt

test:
	$(PY) -m pytest --cov=mailsender --cov-report=term-missing

lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

fmt:
	$(VENV)/bin/ruff format .
	terraform -chdir=$(TF_DIR) fmt -recursive

tf-fmt:
	terraform -chdir=$(TF_DIR) fmt -check -recursive

tf-validate:
	terraform -chdir=$(TF_DIR) init -backend=false -input=false >/dev/null
	terraform -chdir=$(TF_DIR) validate

check: lint test tf-fmt tf-validate

plan:
	terraform -chdir=$(TF_DIR) init -input=false
	terraform -chdir=$(TF_DIR) plan -out=tfplan

apply:
	terraform -chdir=$(TF_DIR) apply tfplan

destroy:
	terraform -chdir=$(TF_DIR) destroy

# Usage: make invoke TO=you@example.com
invoke:
	aws lambda invoke \
		--function-name $$(terraform -chdir=$(TF_DIR) output -raw send_email_function_name) \
		--cli-binary-format raw-in-base64-out \
		--payload '{"to":["$(TO)"],"subject":"MailSender smoke test","text":"Hello from Lambda + SES.","html":"<p>Hello from <b>Lambda + SES</b>.</p>"}' \
		/dev/stdout
