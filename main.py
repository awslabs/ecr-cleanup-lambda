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

try:
    import requests
except ImportError:
    from botocore.vendored import requests

REGION = "ALL"
DRY_RUN = True
IMAGES_TO_KEEP = None
IGNORE_TAGS_REGEX = None


def initialize():
    global REGION
    global DRY_RUN
    global IMAGES_TO_KEEP
    global IGNORE_TAGS_REGEX

    REGION = os.environ.get("REGION", "ALL")

    if os.environ.get("DRY_RUN", "").lower() == "false":
        DRY_RUN = False
    else:
        DRY_RUN = True

    IMAGES_TO_KEEP = int(os.environ.get("IMAGES_TO_KEEP", 100))
    IGNORE_TAGS_REGEX = os.environ.get("IGNORE_TAGS_REGEX", "^$")


def handler(event, context):
    initialize()
    partitions = requests.get(
        "https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/endpoints.json"
    ).json()["partitions"]
    if REGION == "ALL":
        for partition in partitions:
            if partition['partition'] == "aws":
                for endpoint in partition['services']['ecs']['endpoints']:
                    discover_delete_images(endpoint)
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

    # print(repositories)

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

        for image in tagged_images:
            if tagged_images.index(image) >= IMAGES_TO_KEEP:
                for tag in image['imageTags']:
                    if "latest" not in tag and re.compile(IGNORE_TAGS_REGEX).search(tag) is None:
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


def append_to_list(list, id):
    if {"imageDigest": id} not in list:
        list.append({"imageDigest": id})


def append_to_tag_list(list, id):
    if id not in list:
        list.append(id)


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def delete_images(ecr_client, deletesha, deletetag, id, name):
    if len(deletesha) >= 1:
        ## spliting list of images to delete on chunks with 100 images each
        ## http://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_BatchDeleteImage.html#API_BatchDeleteImage_RequestSyntax
        i = 0
        for deletesha_chunk in chunks(deletesha, 100):
            i += 1
            if not DRY_RUN:
                delete_response = ecr_client.batch_delete_image(
                    registryId=id,
                    repositoryName=name,
                    imageIds=deletesha_chunk
                )
                print(delete_response)
            else:
                print("registryId:" + id)
                print("repositoryName:" + name)
                print("Deleting {} chank of images".format(i))
                print("imageIds:", end='')
                print(deletesha_chunk)
    if deletetag:
        print("Image URLs that are marked for deletion:")
        for ids in deletetag:
            print("- {} - {}".format(ids["imageUrl"], ids["pushedAt"]))


# Below is the test harness
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deletes stale ECR images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # We want the user to explicitly opt-in to deleting images so we'll have a
    # mutually-exclusive option group which requires running with either
    # --dry-run or --delete-images
    delete_mode = parser.add_mutually_exclusive_group(required=True)

    delete_mode.add_argument(
        "--dry-run",
        help="Prints the images to be deleted without deleting them",
        action="store_true",
        dest="dry_run",
    )
    delete_mode.add_argument(
        "--delete-images",
        help="Delete the images (cancels --dry-run)",
        action="store_false",
        dest="dry_run",
    )

    parser.add_argument(
        "--images-to-keep", help="Number of image tags to keep", default=100
    )

    parser.add_argument(
        "--region",
        help="AWS region",
        default=os.environ.get("AWS_DEFAULT_REGION", "ALL"),
    )

    parser.add_argument(
        "--ignore-tags-regex", help="Regex of tag names to ignore", default="^$"
    )

    args = parser.parse_args()

    os.environ["REGION"] = args.region
    os.environ["DRY_RUN"] = str(args.dry_run).lower()
    os.environ["IMAGES_TO_KEEP"] = str(args.images_to_keep)
    os.environ["IGNORE_TAGS_REGEX"] = args.ignore_tags_regex

    handler({"None": "None"}, None)
