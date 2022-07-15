TERRAFORM_PLAN_FILE=deploy.tfplan
WORKSPACE=default

plan:
	terraform workspace select $(WORKSPACE)
	terraform plan -out $(TERRAFORM_PLAN_FILE) -var-file="$(WORKSPACE).tfvars"

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy: plan apply
