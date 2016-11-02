from __future__ import print_function
import boto3
import datetime
import argparse
import requests
import json


def handler(event, context):

    if not region:
        partitions = requests.get("https://raw.githubusercontent.com/boto/botocore/develop/botocore/data/endpoints.json").json()['partitions']
        for partition in partitions:
            if partition['partition'] == "aws":
                for endpoint in partition['services']['ecs']['endpoints']:
                    discover_delete_images(endpoint)
    else:
        discover_delete_images(region)

def discover_delete_images(regionname):
    print("Discovering images in "+regionname)
    ecr_client = boto3.client('ecr',region_name=regionname)

    done=False
    marker = None
    repositories = []
    while not done:
        if marker:
            describerepo_response = ecr_client.describe_repositories(maxResults=100,nextToken=marker)
        else :
            describerepo_response = ecr_client.describe_repositories(maxResults=100)

        for repo in describerepo_response['repositories']:
            repositories.append(repo)

        if 'nextToken' in describerepo_response:
            marker = describerepo_response['nextToken']

        else :
            break

    #print(repositories)

    ecs_client = boto3.client('ecs',region_name=regionname)

    listclusters_paginator = ecs_client.get_paginator('list_clusters')
    running_containers = []
    for response_listclusterpaginator in listclusters_paginator.paginate():
        for cluster in response_listclusterpaginator['clusterArns']:
            listtasks_paginator = ecs_client.get_paginator('list_tasks')
            for reponse_listtaskpaginator in listtasks_paginator.paginate(cluster=cluster,desiredStatus='RUNNING'):
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

    #print(running_containers)
    for repository in repositories:
        deletesha = []
        nextmarker = None
        done = False
        images = []
        while not done:
            if nextmarker:
                image_response = ecr_client.describe_images(
                    registryId=repository['registryId'],
                    repositoryName=repository['repositoryName'],
                    nextmarker=nextmarker)
            else:
                image_response = ecr_client.describe_images(
                    registryId=repository['registryId'],
                    repositoryName=repository['repositoryName']
                )

            for image in image_response['imageDetails']:
                images.append(image)

            if 'nextmarker' in image_response['imageDetails']:
                nextmarker = image_response['imageDetails']['nextToken']
            else:
                break

        images.sort(key=lambda k: k['imagePushedAt'],reverse=True)
        for image in images:
            # print(image)
            # timedelta = datetime.date.today() - datetime.datetime.date(image['imagePushedAt'])
            # if timedelta > datetime.timedelta(days=1):
            if images.index(image) > imagestokeep:
                if 'imageTags' in image:
                    for tag in image['imageTags']:
                        if "latest" not in tag:
                            repourl = repository['repositoryUri'] + ":" + tag
                            if running_containers:
                                for running_image in running_containers:
                                    if running_image != repourl:
                                        appendtolist(deletesha, {'imageDigest': image['imageDigest']})
                            else:
                                appendtolist(deletesha, {'imageDigest': image['imageDigest']})


                else:
                    appendtolist(deletesha, {'imageDigest': image['imageDigest']})
        if deletesha:
            delete_images(ecr_client, deletesha, repository['registryId'], repository['repositoryName'])
        else:
            print("Nothing to delete in repository : " + repository['repositoryName'])


def appendtolist(list,id):
    if not {'imageDigest': id} in list:
        list.append({'imageDigest': id})


def delete_images(ecr_client, deletesha, id, name):
    if not dryrunflag:
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
        print("imageIds:",end='')
        print(deletesha)
        print("}")




# Below is the test harness
if __name__ == '__main__':
    request = {"None": "None"}
    parser = argparse.ArgumentParser(description='Deletes stale ECR images')
    parser.add_argument('-dryrun', help='Prints the repository to be deleted without deleting them', default=False, action='store', dest='dryrun')
    parser.add_argument('-daystokeep', help='Number of days to keep the images', default=None,
                        action='store', dest='daystokeep')
    parser.add_argument('-imagestokeep', help='Number of image tags to keep', default=10,
                        action='store', dest='imagestokeep')
    parser.add_argument('-region', help='ECR/ECS region', default=None, action='store', dest='region')

    args = parser.parse_args()
    dryrunflag = args.dryrun
    daystokeep = args.daystokeep
    region = args.region
    imagestokeep = int(args.imagestokeep)
    handler(request, None)
