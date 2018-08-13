# Automated Image Cleanup for Amazon ECR
The Python script and Lambda function described here help clean up images in [Amazon ECR](https://aws.amazon.com/ecr). The script looks for images that are not used in running [Amazon ECS](https://aws.amazon.com/ecs) tasks that can be deleted. You can configure the script to print the image list first to confirm deletions, specify a region, or specify a number of images to keep for potential rollbacks.

## Authenticate with AWS
[Configuring the AWS Command Line Interface.](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)

## Use virtualenv for Python execution

To prevent any problems with your system Python version conflicting with the application, we recommend using virtualenv.

Install Python:
    `pip install python 3`

Install virtualenv:

    $ pip install virtualenv
    $ virtualenv -p PATH_TO_YOUR_PYTHON_3 cloudformtion
    $ virtualenv ~/.virtualenvs/cloudformtion
    $ source ~/.virtualenvs/cloudformtion/bin/activate
    
## Generate the Lambda package

1. CD to the folder that contains main.py.
1. Run the following command:
`pip install -r requirements.txt -t `pwd``
1. Compress the contents of folder (not the folder).
    
## Upload the package to Lambda

1. Run the following command:
`aws lambda create-function --function-name {NAME_OF_FUNCTION} --runtime python2.7 
--role {ARN_NUMBER} --handler main.handler --timeout 15 
--zip-file fileb://{ZIP_FILE_PATH}`
    
## Send the package update to Lambda

1. Run the following command:
    
    `aws lambda update-function-code --function-name {NAME_OF_FUNCTION} --zip-file fileb://{ZIP_FILE_PATH}`


## Examples
Prints the images that are not used by running tasks and which are older than the last 100 versions, in all regions:

`python main.py`


Deletes the images that are not used by running tasks and which are older than the last 100 versions, in all regions:

`python main.py –dryrun False`


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in all regions:

`python main.py –dryrun False –imagestokeep 20`


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in Oregon only:

`python main.py –dryrun False –imagestokeep 20 –region us-west-2`

Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in Oregon only, and ignore image tags that contains `release` or `archive`:

`python main.py –dryrun False –imagestokeep 20 –region us-west-2 -ignoretagsregex release|archive`

