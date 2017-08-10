# Your favorite rapper's favorite wrapper.
.PHONY: default check_defined _check_defined clean build test
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

check_defined = \
    $(strip $(foreach 1,$1, \
        $(call _check_defined,$1,$(strip $(value 2)))))
_check_defined = \
    $(if $(value $1),, \
      $(error Undefined argument $1$(if $2, ($2))))
# End Wrapper

default: cloudformation.yaml deploy
clean:
	@ echo "Cleaning..."
	@ git -C ${mkfile_dir} clean -xqdf

venv: venv/bin/activate

venv/bin/activate: requirements.txt
	@ echo "Building in '${mkfile_dir}/venv'..."
	@ test -d ${mkfile_dir}/venv || virtualenv -q ${mkfile_dir}/venv
	venv/bin/pip install -Ur ${mkfile_dir}/requirements.txt -t ${mkfile_dir}
	@ touch ${mkfile_dir}/venv/bin/activate

cloudformation.yaml: build
	aws cloudformation package \
		--s3-bucket foreflight-lambda \
		--template-file ${mkfile_dir}/lambda-cloudformation.template.yaml \
		--output-template-file ${mkfile_dir}/cloudformation.yaml \
		--force-upload

deploy:
	$(call chef_defined,stack_name)
	aws cloudformation deploy --template-file ${mkfile_dir}/cloudformation.yaml --capabilities CAPABILITY_IAM --stack-name ${stack_name}

