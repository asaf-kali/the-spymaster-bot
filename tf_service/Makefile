DEL_COMMAND=gio trash
TERRAFORM_PLAN_FILE=deploy.tfplan
LAMBDA_ZIP_FILE=the-spymaster-bot.zip
LAYER_ZIP_FILE=the-spymaster-bot-layer.zip

plan:
	terraform plan -out $(TERRAFORM_PLAN_FILE)

apply:
	terraform apply $(TERRAFORM_PLAN_FILE)

deploy:
	@make plan --no-print-directory
	@make apply --no-print-directory
	$(DEL_COMMAND) $(LAMBDA_ZIP_FILE) $(LAYER_ZIP_FILE)
