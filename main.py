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
import os
import argparse
import boto3
import requests


REGION = None
DRYRUN = None
IMAGES_TO_KEEP = None

def initialize():
    global REGION
    global DRYRUN
    global IMAGES_TO_KEEP

    REGION = os.environ.get('REGION', "None")
    DRYRUN = os.environ.get('DRYRUN', "false").lower()
    if DRYRUN == "false":
        DRYRUN = False
    else:
        DRYRUN = True
    IMAGES_TO_KEEP = int(os.environ.get('IMAGES_TO_KEEP', 100))



def handler(event, context):
    initialize()
    if REGION == "None":
        partitions = requests.get("https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/endpoints.json").json()['partitions']
        for partition in partitions:
            if partition['partition'] == "aws":
                for endpoint in partition['services']['ecs']['endpoints']:
                    discover_delete_images(endpoint)
    else:
        discover_delete_images(REGION)

def discover_delete_images(regionname):
    print("Discovering images in "+regionname)
    ecr_client = boto3.client('ecr', region_name=regionname)

    repositories = []
    describerepo_paginator = ecr_client.get_paginator('describe_repositories')
    for response_listrepopaginator in describerepo_paginator.paginate():
        for repo in response_listrepopaginator['repositories']:
            repositories.append(repo)

    #print(repositories)

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

    print("Images that are running")
    print(running_containers)
    for repository in repositories:
        print ("------------------------")
        print("Starting with repository :"+repository['repositoryUri'])
        deletesha = []
        deletetag = []
        images = []
        describeimage_paginator = ecr_client.get_paginator('describe_images')
        for response_describeimagepaginator in describeimage_paginator.paginate(
                registryId=repository['registryId'],
                repositoryName=repository['repositoryName']):
            for image in response_describeimagepaginator['imageDetails']:
                images.append(image)

        images.sort(key=lambda k: k['imagePushedAt'], reverse=True)

        #Get ImageDigest from ImageURL for running images. Do this for every repository
        running_sha = []
        for image in images:
            if 'imageTags' in image:
                for tag in image['imageTags']:
                    imageurl = repository['repositoryUri'] + ":" + tag
                    for runningimages in running_containers:
                        if imageurl == runningimages:
                            if imageurl not in running_sha:
                                running_sha.append(image['imageDigest'])
        print("Total number of images found: {}".format(len(images)))
        for image in images:
            if images.index(image) >= IMAGES_TO_KEEP:
                if 'imageTags' in image:
                    for tag in image['imageTags']:
                        if "latest" not in tag:
                            if running_sha:
                                if image['imageDigest'] not in running_sha:
                                    appendtolist(deletesha, image['imageDigest'])
                                    appendtotaglist(deletetag, {"imageUrl": repository['repositoryUri'] + ":" + tag, "pushedAt": image["imagePushedAt"]})
                            else:
                                appendtolist(deletesha, image['imageDigest'])
                                appendtotaglist(deletetag, {"imageUrl": repository['repositoryUri'] + ":" + tag, "pushedAt": image["imagePushedAt"]})
                else:
                    appendtolist(deletesha, image['imageDigest'])
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


def appendtolist(list, id):
    if not {'imageDigest': id} in list:
        list.append({'imageDigest': id})

def appendtotaglist(list, id):
    if not id in list:
        list.append(id)


def delete_images(ecr_client, deletesha, deletetag, id, name):
    if not DRYRUN:
        delete_response = ecr_client.batch_delete_image(
            registryId=id,
            repositoryName=name,
            imageIds=deletesha
        )
        print (delete_response)
    else:
        print("{")
        print("registryId:"+id)
        print("repositoryName:"+name)
        print("imageIds:", end='')
        print(deletesha)
        print("}")
    if deletetag:
        print("Image URLs that are marked for deletion:")
        for ids in deletetag:
            print("- {} - {}".format(ids["imageUrl"], ids["pushedAt"]))

# Below is the test harness
if __name__ == '__main__':
    request = {"None": "None"}
    parser = argparse.ArgumentParser(description='Deletes stale ECR images')
    parser.add_argument('-dryrun', help='Prints the repository to be deleted without deleting them', default='true', action='store', dest='dryrun')
    parser.add_argument('-imagestokeep', help='Number of image tags to keep', default='100', action='store', dest='imagestokeep')
    parser.add_argument('-region', help='ECR/ECS region', default=None, action='store', dest='region')

    args = parser.parse_args()
    if args.region:
        os.environ["REGION"] = args.region
    else:
        os.environ["REGION"] = "None"
    os.environ["DRYRUN"] = args.dryrun.lower()
    os.environ["IMAGES_TO_KEEP"] = args.imagestokeep
    handler(request, None)
