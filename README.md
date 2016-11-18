#Lambda function for automated cleanup of Amazon Elastic Container Registry

## Authentication with AWS
Use your preferred means as explained at http://docs.aws.amazon.com/AWSJavaScriptSDK/guide/node-configuring.html

## Instructions to use the VirtualEnv for Python execution

    1) Just to prevent or causing any problems with your system python version conflicting 
    with the application, use of virtual env is recommended
    2) pip install python 3
    3) Install virtualenv by virtualenv

    $ pip install virtualenv
    $ virtualenv -p PATH_TO_YOUR_PYTHON_3 cloudformtion
    $ virtualenv ~/.virtualenvs/cloudformtion
    $ source ~/.virtualenvs/cloudformtion/bin/activate
    
## Package generation for lambda

    1) CD in the folder, which has main.py
    2) Run -->  pip install -r requirements.txt -t {THE_FOLDER_PATH}
    3) Compress the contents of folder (and not the folder)
    
##Package Upload to Lambda

    1) Run the below command
    
    aws lambda create-function --function-name {NAME_OF_FUNCTION} --runtime python2.7 
    --role {ARN_NUMBER} --handler main.handler --timeout 15 
    --zip-file fileb://{ZIP_FILE_PATH}
    
##Package Update to Lambda

    1) Run the below command
    
    aws lambda update-function-code --function-name {NAME_OF_FUNCTION} --zip-file fileb://{ZIP_FILE_PATH}


##Examples
Prints the images that are not used by running tasks and which are older than the last 100 versions, in all regions:
python main.py


Deletes the images that are not used by running tasks and which are older than the last 100 versions, in all regions:
python main.py –dryrun False


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in all regions:
python main.py –dryrun False –imagestokeep 20


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in Oregon only:
python main.py –dryrun False –imagestokeep 20 –region us-west-2


