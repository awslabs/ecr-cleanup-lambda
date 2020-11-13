# Automated Image Cleanup for Amazon ECR
The Python script and Lambda function described here help clean up images in [Amazon ECR](https://aws.amazon.com/ecr).
- The script looks for images that are not used in running [Amazon ECS](https://aws.amazon.com/ecs) tasks that can be deleted. 
- Only looks images in repos specified in GitHubActions env var ECR_REPOS_LIFECYCLE ex: ECR_REPOS_LIFECYCLE='apache, nginx'
- You can configure the script to print the image list first to confirm deletions, specify a region, or specify a number of images to keep for potential rollbacks with DRYRUN=true
- You can skip images followin a REGEX in their tag.

## Usage in local

Install Python:
    `pip install python 3`

Getting info about local env:
    `which python3`

Install virtualenv:

    pip install virtualenv
    virtualenv --python=/usr/local/bin/python3 ~/venv-ecr-cleanup-lambda
    source ~/venv-ecr-cleanup-lambda/bin/activate
    
## Install dependencies

`pip install -r requirements.txt`

## Example

Deletes the images that:
- are not used by ECS running tasks .
- are older than the last 20 versions (in each repository).
- in Oregon only.
- ignore image tags that contains `release` or `archive`.
- skip images with tags that contain alpine and apache.

`python main.py –dryrun False –imagestokeep 20 –region us-west-2 -ignoretagsregex 'release|archive' -ecr_repos_lifecycle 'alpine,apache'`


## Credits

Fork of awslabs/ecr-cleanup-lambda adding functionality of ECR_REPOS_LIFECYCLE var.