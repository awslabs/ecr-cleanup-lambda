#Automated Image Cleanup for Amazon ECR

The Python script and Lambda function described here help clean up images in [Amazon ECR](https://aws.amazon.com/ecr). The script looks for images that are not used in running [Amazon ECS](https://aws.amazon.com/ecs) tasks that can be deleted. You can configure the script to print the image list first to confirm deletions, specify a region, or specify a number of images to keep for potential rollbacks.

## Authenticate with AWS
[Configuring the AWS Command Line Interface.](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)

## Generate and deploy the Lambda package

1. CD to the folder that contains main.py.
1. Run the following command: `make s3_bucket=my-bucket stack_name=ecr-cleanup`
1. You'll see output similar to:

        $ make s3_bucket=my-bucket stack_name=ecr-cleanup
        $ make s3_bucket=foreflight-temp stack_name=ecr-cleanup
        aws cloudformation package \
        		--s3-bucket foreflight-temp \
        		--template-file /Users/djimenez/src/ForeFlight/metal/lambda/ecr-cleanup-lambda/lambda-cloudformation.template.yaml \
        		--output-template-file /Users/djimenez/src/ForeFlight/metal/lambda/ecr-cleanup-lambda/cloudformation.yaml \
        		--force-upload
        Uploading to 14d6a5936698c71b92c8609c68cb51f2  13583057 / 13583057.0  (100.00%)
        Successfully packaged artifacts and wrote output template to file /Users/djimenez/src/ForeFlight/metal/lambda/ecr-cleanup-lambda/cloudformation.yaml.
        Execute the following command to deploy the packaged template
        aws cloudformation deploy --template-file /Users/djimenez/src/ForeFlight/metal/lambda/ecr-cleanup-lambda/cloudformation.yaml --stack-name <YOUR STACK NAME>
        aws cloudformation deploy --template-file /Users/djimenez/src/ForeFlight/metal/lambda/ecr-cleanup-lambda/cloudformation.yaml --capabilities CAPABILITY_IAM --stack-name ecr-cleanup
        Waiting for changeset to be created..
        Waiting for stack create/update to complete
        Successfully created/updated stack - ecr-cleanup

## Examples
Prints the images that are not used by running tasks and which are older than the last 100 versions, in all regions:

`python main.py`


Deletes the images that are not used by running tasks and which are older than the last 100 versions, in all regions:

`python main.py –dryrun False`


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in all regions:

`python main.py –dryrun False –imagestokeep 20`


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in Oregon only:

`python main.py –dryrun False –imagestokeep 20 –region us-west-2`


