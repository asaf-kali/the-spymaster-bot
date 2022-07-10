TERRAFORM_PLAN_FILE=deploy.tfplan
ENV=default

plan:
	terraform workspace select $(ENV)
	terraform plan -out $(TERRAFORM_PLAN_FILE) -var-file="$(ENV).tfvars"

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy: plan apply
