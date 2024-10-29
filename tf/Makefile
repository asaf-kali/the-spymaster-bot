TERRAFORM_PLAN_FILE=deploy.tfplan
WORKSPACE=default
AWS_REGION=us-east-1

update:
	terraform get -update

upgrade:
	terraform init -upgrade

refresh:
	terraform workspace select $(WORKSPACE)
	terraform refresh \
		-var-file="$(WORKSPACE).tfvars" \

plan:
	terraform workspace select $(WORKSPACE)
	terraform plan \
		-out $(TERRAFORM_PLAN_FILE) \
		-var-file="$(WORKSPACE).tfvars" \
		-var="aws_region=$(AWS_REGION)"

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy: plan apply
