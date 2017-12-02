import http.client, urllib.request, urllib.parse, urllib.error, base64, json, os, requests
from unsplash.api import Api
from unsplash.auth import Auth
from unsplash.photo import Photo
from operator import itemgetter


def azureAnalysis(photo_url, subscription_key):

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

    body = "{'url':'%s'}" %photo_url

    # Execute the REST API call and get the response.
    conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
    conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
    response = conn.getresponse()
    data_bytes = response.read()
    data = json.loads(data_bytes.decode())
    print(data)
    tags = data['description']['tags']

    return tags

def unsplashRequest(tag, api, photo_worker):
    photos = api.search.photos(tag)['results']

    download_urls = []
    for photo in photos:
        download_urls.append(photo_worker.download(photo.id)['url'])

    return download_urls

def jaccard(A, B):
    numer = len(A & B)
    denom = len(A + B)
    return numer/denom

def main():
    #get unsplash API stuff
    client_id = os.environ.get('UNSPLASH_ID', None)
    client_secret = os.environ.get('UNSPLASH_SECRET', None)
    redirect_uri = ""
    code = ""

    auth = Auth(client_id, client_secret, redirect_uri, code=code)
    api = Api(auth)

    photo_worker = Photo(api=api)

    # get env variable API key
    azure_key = os.environ.get('AZURE_KEY', None)

    orig_tags = azureAnalysis('http://sheepmountain.com/wp-content/uploads/2016/01/20150131-DSC_0640-3-1500x700.jpg',
                              azure_key)

    '''
    download_urls = unsplashRequest(orig_tags[0], api, photo_worker)
    for url in download_urls:
        print(url)
        print(azureAnalysis(url, azure_key))
    '''

    tagged_photos = {} # a dict which maps the url where we can find a photo to the tags of that photo
    for tag in orig_tags:
        download_urls = unsplashRequest(tag, api, photo_worker)
        for url in download_urls:
            tags = azureAnalysis(url, azure_key)
            tagged_photos[url] = tags

    scores = {}
    for url, tags in tagged_photos.items():
        tags = set(tags)
        scores[url] = jaccard(orig_tags, tags)

    best_url = max(scores, key=scores.get)
    urllib.request.urlretrieve(best_url, 'BEST.jpeg')


if __name__ == '__main__':
    main()