DEL_COMMAND=gio trash
TERRAFORM_PLAN_FILE=deploy.tfplan

plan:
	terraform plan -out $(TERRAFORM_PLAN_FILE)

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy:
	@make plan --no-print-directory
	@make apply --no-print-directory
