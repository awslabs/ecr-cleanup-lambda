# Automated Image Cleanup for Amazon ECR
The Python script and Lambda function described here help clean up images in [Amazon ECR](https://aws.amazon.com/ecr).
- The script looks for images that are not used in running [Amazon ECS](https://aws.amazon.com/ecs) tasks that can be deleted. 
- Only looks images in repos specified in GitHubActions env var ECR_REPOS_LIFECYCLE.
- You can configure the script to print the image list first to confirm deletions, specify a region, or specify a number of images to keep for potential rollbacks.

## Usage in local

To prevent any problems with your system Python version conflicting with the application, we recommend using virtualenv.

Install Python:
    `pip install python 3`

Getting info about local env:
    `which python3`

Install virtualenv:

    $ pip install virtualenv
    $ virtualenv --python=/usr/local/bin/python3 ~/venv-ecr-cleanup-lambda
    $ source ~/venv-ecr-cleanup-lambda/bin/activate
    
## Install dependencies

`pip install -r requirements.txt`

    
## Examples
Prints the images that are not used by running tasks and which are older than the last 100 versions, in all regions in ECR repos named alpine and apache:

`python main.py -ecr_repos_lifecycle 'alpine,apache'`


Deletes the images that are not used by running tasks and which are older than the last 100 versions, in all regions:

`python main.py –dryrun False -ecr_repos_lifecycle 'alpine,apache'`


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in all regions:

`python main.py –dryrun False –imagestokeep 20 -ecr_repos_lifecycle 'alpine,apache'`


Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in Oregon only:

`python main.py –dryrun False –imagestokeep 20 –region us-west-2 -ecr_repos_lifecycle 'alpine,apache'`

Deletes the images that are not used by running tasks and which are older than the last 20 versions (in each repository), in Oregon only, and ignore image tags that contains `release` or `archive`:

`python main.py –dryrun False –imagestokeep 20 –region us-west-2 -ignoretagsregex release|archive -ecr_repos_lifecycle 'alpine,apache'`

