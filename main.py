'''
Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with
the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and
limitations under the License.
'''
from __future__ import print_function

import argparse
import os
import re
import boto3

REGION = None
DRYRUN = None
IMAGES_TO_KEEP = None
IGNORE_TAGS_REGEX = None


def initialize():
    global REGION
    global DRYRUN
    global IMAGES_TO_KEEP
    global IGNORE_TAGS_REGEX

    REGION = os.environ.get('REGION', "None")
    DRYRUN = os.environ.get('DRYRUN', "false").lower()
    if DRYRUN == "false":
        DRYRUN = False
    else:
        DRYRUN = True
    IMAGES_TO_KEEP = int(os.environ.get('IMAGES_TO_KEEP', 100))
    IGNORE_TAGS_REGEX = os.environ.get('IGNORE_TAGS_REGEX', "^$")

def handler(event, context):
    initialize()
    if REGION == "None":
        ec2_client = boto3.client('ec2')
        available_regions = ec2_client.describe_regions()['Regions']
        for region in available_regions:
            discover_delete_images(region['RegionName'])
    else:
        discover_delete_images(REGION)


def discover_delete_images(regionname):
    print("Discovering images in " + regionname)
    ecr_client = boto3.client('ecr', region_name=regionname)

    repositories = []
    describe_repo_paginator = ecr_client.get_paginator('describe_repositories')
    for response_listrepopaginator in describe_repo_paginator.paginate():
        for repo in response_listrepopaginator['repositories']:
            repositories.append(repo)

    ecs_client = boto3.client('ecs', region_name=regionname)

    listclusters_paginator = ecs_client.get_paginator('list_clusters')
    running_containers = []
    for response_listclusterpaginator in listclusters_paginator.paginate():
        for cluster in response_listclusterpaginator['clusterArns']:
            listtasks_paginator = ecs_client.get_paginator('list_tasks')
            for reponse_listtaskpaginator in listtasks_paginator.paginate(cluster=cluster, desiredStatus='RUNNING'):
                if reponse_listtaskpaginator['taskArns']:
                    describe_tasks_list = ecs_client.describe_tasks(
                        cluster=cluster,
                        tasks=reponse_listtaskpaginator['taskArns']
                    )

                    for tasks_list in describe_tasks_list['tasks']:
                        if tasks_list['taskDefinitionArn'] is not None:
                            response = ecs_client.describe_task_definition(
                                taskDefinition=tasks_list['taskDefinitionArn']
                            )
                            for container in response['taskDefinition']['containerDefinitions']:
                                if '.dkr.ecr.' in container['image'] and ":" in container['image']:
                                    if container['image'] not in running_containers:
                                        running_containers.append(container['image'])

    print("Images that are running:")
    for image in running_containers:
        print(image)

    for repository in repositories:
        print("------------------------")
        print("Starting with repository :" + repository['repositoryUri'])
        deletesha = []
        deletetag = []
        tagged_images = []

        describeimage_paginator = ecr_client.get_paginator('describe_images')
        for response_describeimagepaginator in describeimage_paginator.paginate(
                registryId=repository['registryId'],
                repositoryName=repository['repositoryName']):
            for image in response_describeimagepaginator['imageDetails']:
                if 'imageTags' in image:
                    tagged_images.append(image)
                else:
                    append_to_list(deletesha, image['imageDigest'])

        print("Total number of images found: {}".format(len(tagged_images) + len(deletesha)))
        print("Number of untagged images found {}".format(len(deletesha)))

        tagged_images.sort(key=lambda k: k['imagePushedAt'], reverse=True)

        # Get ImageDigest from ImageURL for running images. Do this for every repository
        running_sha = []
        for image in tagged_images:
            for tag in image['imageTags']:
                imageurl = repository['repositoryUri'] + ":" + tag
                for runningimages in running_containers:
                    if imageurl == runningimages:
                        if imageurl not in running_sha:
                            running_sha.append(image['imageDigest'])

        print("Number of running images found {}".format(len(running_sha)))
        ignore_tags_regex = re.compile(IGNORE_TAGS_REGEX)
        for image in tagged_images:
            if tagged_images.index(image) >= IMAGES_TO_KEEP:
                for tag in image['imageTags']:
                    if "latest" not in tag and ignore_tags_regex.search(tag) is None:
                        if not running_sha or image['imageDigest'] not in running_sha:
                            append_to_list(deletesha, image['imageDigest'])
                            append_to_tag_list(deletetag, {"imageUrl": repository['repositoryUri'] + ":" + tag,
                                                           "pushedAt": image["imagePushedAt"]})
        if deletesha:
            print("Number of images to be deleted: {}".format(len(deletesha)))
            delete_images(
                ecr_client,
                deletesha,
                deletetag,
                repository['registryId'],
                repository['repositoryName']
            )
        else:
            print("Nothing to delete in repository : " + repository['repositoryName'])


def append_to_list(image_digest_list, repo_id):
    if not {'imageDigest': repo_id} in image_digest_list:
        image_digest_list.append({'imageDigest': repo_id})


def append_to_tag_list(tag_list, tag_id):
    if not tag_id in tag_list:
        tag_list.append(tag_id)


def chunks(repo_list, chunk_size):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(repo_list), chunk_size):
        yield repo_list[i:i + chunk_size]


def delete_images(ecr_client, deletesha, deletetag, repo_id, name):
    if len(deletesha) >= 1:
        ## spliting list of images to delete on chunks with 100 images each
        ## http://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_BatchDeleteImage.html#API_BatchDeleteImage_RequestSyntax
        i = 0
        for deletesha_chunk in chunks(deletesha, 100):
            i += 1
            if not DRYRUN:
                delete_response = ecr_client.batch_delete_image(
                    registryId=repo_id,
                    repositoryName=name,
                    imageIds=deletesha_chunk
                )
                print(delete_response)
            else:
                print("registryId:" + repo_id)
                print("repositoryName:" + name)
                print("Deleting {} chank of images".format(i))
                print("imageIds:", end='')
                print(deletesha_chunk)
    if deletetag:
        print("Image URLs that are marked for deletion:")
        for ids in deletetag:
            print("- {} - {}".format(ids["imageUrl"], ids["pushedAt"]))


# Below is the test harness
if __name__ == '__main__':
    REQUEST = {"None": "None"}
    PARSER = argparse.ArgumentParser(description='Deletes stale ECR images')
    PARSER.add_argument('-dryrun', help='Prints the repository to be deleted without deleting them', default='true',
                        action='store', dest='dryrun')
    PARSER.add_argument('-imagestokeep', help='Number of image tags to keep', default='100', action='store',
                        dest='imagestokeep')
    PARSER.add_argument('-region', help='ECR/ECS region', default=None, action='store', dest='region')
    PARSER.add_argument('-ignoretagsregex', help='Regex of tag names to ignore', default="^$", action='store', dest='ignoretagsregex')

    ARGS = PARSER.parse_args()
    if ARGS.region:
        os.environ["REGION"] = ARGS.region
    else:
        os.environ["REGION"] = "None"
    os.environ["DRYRUN"] = ARGS.dryrun.lower()
    os.environ["IMAGES_TO_KEEP"] = ARGS.imagestokeep
    os.environ["IGNORE_TAGS_REGEX"] = ARGS.ignoretagsregex
    handler(REQUEST, None)
