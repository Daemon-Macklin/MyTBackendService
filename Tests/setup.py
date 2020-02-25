# importing the requests library
import requests
password = "password123"
userName = "jsonTestUser2"
email = userName + "@gmail.com"
uid = ""

# defining the api-endpoint
API_ENDPOINT = "http://87.44.16.158:5000/v1/"

def createUser():
	# data to be sent to api
	createData = {
		"userName" : userName,
		"email" : email,
		"password" : password
	}

	# sending post request and saving response as response object
	response = requests.post(url = API_ENDPOINT + "users/create", json = createData)

	return response.json()

def createCreds():
	credsData = {
		"name" : "AWS",
		"accessKey" : "qwertyuioplkjhgfdsaz",
		"secretKey" : "qwertyuioplkjhgfdsaz",
		"uid" : uid,
		"password" : password
	}

	response = requests.post(url = API_ENDPOINT + "credentials/create/aws", json = credsData)

	return response.json()

def createSpace():
	spaceData = {
		"password" : "jack",
		"cloudService" : "aws",
		"spaceName" : "iot life",
		"uid": uid,
		"cid": cid
	}

	response = requests.post(url = API_ENDPOINT + "spaces/create", json = spaceData)

	return response.json()["id"]

def createPlatform():
	platformData = {
		"password" : "jack",
		"cloudService" : "aws",
		"platformName" : "iot2",
		"uid": uid,
		"sid": cid
	}

	response = request.post(url=API_ENDPOINT + "platform/create", json=platformData)

	return response.json()
