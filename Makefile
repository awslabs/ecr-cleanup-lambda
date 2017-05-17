.PHONY: default clean deploy stack_name s3_bucket

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

default: cloudformation.yaml deploy

venv: venv/bin/activate

venv/bin/activate: requirements.txt
	@ echo "Building in '${mkfile_dir}/venv'..."
	@ test -d ${mkfile_dir}/venv || virtualenv -q ${mkfile_dir}/venv
	venv/bin/pip install -Ur ${mkfile_dir}/requirements.txt -t ${mkfile_dir}
	@ touch ${mkfile_dir}/venv/bin/activate

cloudformation.yaml: venv s3_bucket
	aws cloudformation package \
		--s3-bucket ${s3_bucket} \
		--template-file ${mkfile_dir}/lambda-cloudformation.template.yaml \
		--output-template-file ${mkfile_dir}/cloudformation.yaml \
		--force-upload

deploy: stack_name
	aws cloudformation deploy --template-file ${mkfile_dir}/cloudformation.yaml --capabilities CAPABILITY_IAM --stack-name ${stack_name}

clean:
	@ echo "Cleaning..."
	@ git -C ${mkfile_dir} clean -xqdf

s3_bucket:
ifndef s3_bucket
	$(error `s3_bucket` is not set, i.e. 'example-bucket'.)
endif


stack_name:
ifndef stack_name
	$(error stack_name is not set, i.e. 'ecr-cleanup-lambda'.)
endif
