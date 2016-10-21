from __future__ import print_function
import boto3
import datetime
import argparse


def handler(event, context):
    ecr_client = boto3.client('ecr')
    repositories = ecr_client.describe_repositories(maxResults=100)
    #print(repositories)

    ecs_client = boto3.client('ecs')

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
            timedelta = datetime.date.today() - datetime.datetime.date(image['imagePushedAt'])
            if timedelta > datetime.timedelta(days=1):
                if 'imageTags' in image:
                    if "latest" not in image['imageTags'][0]:
                        repourl = repository['repositoryUri']+":"+image['imageTags'][0]
                        if running_containers:
                            for running_image in running_containers:
                                if running_image != repourl:
                                    deletesha.append({'imageDigest': image['imageDigest']})
                        else:
                            deletesha.append({'imageDigest': image['imageDigest']})
                else:
                    deletesha.append({'imageDigest': image['imageDigest']})

        if deletesha:
            delete_images(ecr_client, deletesha, repository['registryId'], repository['repositoryName'])
        else:
            print("Nothing to delete in repository : "+repository['repositoryName'])



def delete_images(ecr_client, deletesha, id, name):
    if not dryrunflag:
        delete_response = ecr_client.batch_delete_image(
            registryId=id,
            repositoryName=name,
            imageIds=deletesha
         )
        print (delete_response)
    else:
        printer = "{registryId:"+id+",repositoryName:"+name+",imageIds:"+".".join(deletesha)+"}"
        print(printer)




# Below is the test harness
if __name__ == '__main__':
    request = {"None": "None"}
    parser = argparse.ArgumentParser(description='Deletes stale ECR images')
    parser.add_argument('-dryrun', help='Prints the repository to be deleted without deleting them', default=False, action='store', dest='dryrun')
    args = parser.parse_args()
    dryrunflag = args.dryrun
    handler(request, None)
