import requests, base64, os

azure_key = os.environ.get('AZURE_KEY', None)

headers = {
    # Request headers.
    'Content-Type': 'application/json',

    # NOTE: Replace the "Ocp-Apim-Subscription-Key" value with a valid subscription key.
    'Ocp-Apim-Subscription-Key': azure_key,
}

params = {
    # Request parameters. All of them are optional.
    'visualFeatures': 'Categories',
    'details': 'Celebrities',
    'language': 'en',
}

# Replace the three dots below with the URL of a JPEG image of a celebrity.
body = {'url':'...'
}

try:
    # NOTE: You must use the same location in your REST call as you used to obtain your subscription keys.
    #   For example, if you obtained your subscription keys from westus, replace "westcentralus" in the 
    #   URL below with "westus".
    response = requests.post(url = 'https://westcentralus.api.cognitive.microsoft.com/vision/v1.0/analyze',
                             headers = headers,
                             params = params,
                             json = body)
    data = response.json()
    print(data)
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))
####################################
