import http.client, urllib.request, urllib.parse, urllib.error, base64, json, os, requests
from requests.auth import HTTPBasicAuth

def azureAnalysis(subscription_key):

    uri_base = 'westcentralus.api.cognitive.microsoft.com'

    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }

    params = urllib.parse.urlencode({
        # Request parameters
        'visualFeatures': 'Description',
        'language': 'en',
    })

    body = "{'url':'http://sheepmountain.com/wp-content/uploads/2016/01/20150131-DSC_0640-3-1500x700.jpg'}"

    # Execute the REST API call and get the response.
    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
    conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
    response = conn.getresponse()
    data_bytes = response.read()
    data = json.loads(data_bytes.decode())
    tags = data['description']['tags']


    return tags

def unsplashRequest(tags, unsplash_key):
    r = requests.get('https://api.unsplash.com/search/photos?page=1&query=%s?client_id=%s' %(tags[0], unsplash_key))
    print(r)


# get env variable API key
azure_key = os.environ.get('AZURE_KEY', None)
unsplash_key = os.environ.get('UNSPLASH_KEY', None)

tags = azureAnalysis(azure_key)
unsplashRequest(tags, unsplash_key)
