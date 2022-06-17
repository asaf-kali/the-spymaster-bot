TERRAFORM_PLAN_FILE=deploy.tfplan

plan:
	terraform plan -out $(TERRAFORM_PLAN_FILE)

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)
