from flask import Blueprint, request
import response as Response
import terraform as tf
import ansible as ab
from app.config import URL_PREFIX
from shutil import copyfile
import os
import time

platform_crud = Blueprint('platform_crud', __name__, url_prefix=URL_PREFIX)


# End Point to create platform. Takes in a number of requirements
# 1. Name for platform
# 2. Cloud service to deploy to
@platform_crud.route('platform/create', methods=["Post"])
def createPlatform():
    data = request.json
    platformName = None
    cloudService = None

    print(data)
    if 'platformName' in data:
        platformName = data["platformName"]
    else:
        return Response.make_error_resp(msg="Platform Requires Name", code=400)

    if 'cloudService' in data:
        cloudService = data['cloudService']
    else:
        return Response.make_error_resp(msg="Cloud Service Choice is required", code=400)

    safePlaformName = platformName.replace('/', '_')
    platformPath = os.path.join("platforms", safePlaformName)
    try:
        os.makedirs(platformPath)
    except FileExistsError as e:
        print(e)
        return Response.make_error_resp(msg="Platform Name already used", code=400)
    except Exception as e:
        print(e)
        return Response.make_error_resp(msg="Error Creating Platform Directory", code=400)

    tfPath = ""
    if cloudService == "aws":
        tfPath = "terraformScripts/createPlatform/aws"
    elif cloudService == "openstack":
        tfPath = "terraformScripts/createPlatform/openstack"

    requiredFiles = ["deploy.tf", "provider.tf", "variables.tf"]

    for file in requiredFiles:
        copyfile(tfPath + "/" + file, platformPath + "/" + file)

    initResultCode = tf.init(platformPath)

    output, createResultCode = tf.create(platformPath)

    print(createResultCode)
    print(output)
    if createResultCode != 0:
        # Add destroy function here
        return Response.make_error_resp(msg="Error Creating Infrastructure", code=400)

    isUp = serverCheck(output["instance_ip_address"]["value"])

    if not isUp:
        return Response.make_error_resp(msg="Error Contacting Server")

    ansiblePath = "ansiblePlaybooks/createPlatform"
    output, error = ab.configServer(output["instance_ip_address"]["value"], ansiblePath)

    print(output)
    print(error)

    return Response.make_success_resp("Whoops...This function is not finished")


# ==============Helper Functions=============#

def serverCheck(floating_ip):
    counter = 0
    isUp = False
    while counter < 12:
        response = os.system("ping -c 1 " + floating_ip)

        if response == 0:
            print("Host is up")
            time.sleep(10)
            isUp = True
            break
        else:
            print("Host is down - Waiting 10 seconds")
            time.sleep(10)
            counter += 1

    return isUp
