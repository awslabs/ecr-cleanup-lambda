from __future__ import print_function
import boto3
import datetime
import argparse


def handler(event, context):
    ecs_regions = ['us-east-1','us-east-2','us-west-1','us-west-2','eu-central-1',
                   'eu-west-1','ap-northeast-1','ap-southeast-1','ap-southeast-2']
    #print(region_response)
    for region in ecs_regions:
        discover_delete_images(region)

def discover_delete_images(regionname):
    print("Discovering images in "+regionname)
    ecr_client = boto3.client('ecr',region_name=regionname)
    repositories = ecr_client.describe_repositories(maxResults=100)
    #print(repositories)

    ecs_client = boto3.client('ecs',region_name=regionname)

    list_clusters = ecs_client.list_clusters()
    running_containers = []
    for cluster in list_clusters['clusterArns']:
        tasks_list = ecs_client.list_tasks(
            cluster=cluster,
            desiredStatus='RUNNING'
        )
        if tasks_list['taskArns']:
            describe_tasks_list = ecs_client.describe_tasks(
                cluster=cluster,
                tasks=tasks_list['taskArns']
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
    for repository in repositories['repositories']:
        deletesha = []
        images = ecr_client.describe_images(
            registryId=repository['registryId'],
            repositoryName=repository['repositoryName']
        )
        #print(images)
        for image in images['imageDetails']:
            #print(image)
            #timedelta = datetime.date.today() - datetime.datetime.date(image['imagePushedAt'])
            #if timedelta > datetime.timedelta(days=1):
                if 'imageTags' in image:
                    if "latest" not in image['imageTags'][0]:
                        repourl = repository['repositoryUri']+":"+image['imageTags'][0]
                        if running_containers:
                            for running_image in running_containers:
                                if running_image != repourl:
                                    appendtolist(deletesha,{'imageDigest': image['imageDigest']})
                        else:
                            appendtolist(deletesha, {'imageDigest': image['imageDigest']})
                else:
                    appendtolist(deletesha, {'imageDigest': image['imageDigest']})

        if deletesha:
            delete_images(ecr_client, deletesha, repository['registryId'], repository['repositoryName'])
        else:
            print("Nothing to delete in repository : "+repository['repositoryName'])

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

    args = parser.parse_args()
    dryrunflag = args.dryrun
    daystokeep = args.daystokeep
    handler(request, None)
