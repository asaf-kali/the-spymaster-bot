TERRAFORM_PLAN_FILE=deploy.tfplan
WORKSPACE=default
AWS_REGION=us-east-1

plan:
	terraform workspace select $(WORKSPACE)

	terraform plan \
	-out $(TERRAFORM_PLAN_FILE) \
	-var-file="$(WORKSPACE).tfvars" \
	-var="aws_region=$(AWS_REGION)"

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy: plan apply
