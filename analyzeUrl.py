import http.client, urllib.request, urllib.parse, urllib.error, base64, json, os, requests
from unsplash.api import Api
from unsplash.auth import Auth
from unsplash.photo import Photo
import time
from difflib import SequenceMatcher
import keyworder


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

    need_tags = True
    while need_tags:
    # Execute the REST API call and get the response.
        conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
        conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
        response = conn.getresponse()
        data_bytes = response.read()
        data = json.loads(data_bytes.decode())
        print(data)

        if 'statusCode' in data.keys():
            if data['statusCode'] == 429:
                time.sleep(10)
        else:
            tags = data['description']['tags']
            captions = data['description']['captions']
            need_tags = False

    return tags, captions


def unsplashRequest(tag, api, photo_worker):
    photos = api.search.photos(tag, per_page=15)['results']

    download_urls = []
    for photo in photos:
        download_urls.append(photo_worker.download(photo.id)['url'])

    return download_urls


def jaccard(A, B):
    A = set(A)
    B = set(B)

    numer = len(A & B)
    denom = len(A | B)
    return numer/denom


def write_picture_info(file, heading, url, tags, captions):
    # record some data
    file.write(heading + '\n')
    file.write(url)
    file.write('\n')
    file.write(str(tags))
    if captions is not None:
        file.write('\n')
        file.write(str(captions).strip('[{}]'))
    file.write('\n\n')

def main(orig_photo_url, text):
    # get stuff so that we can write results to a file.
    results_file = open('trial5.output', 'w')

    #get unsplash API stuff
    client_id = os.environ.get('UNSPLASH_ID', None)
    client_secret = os.environ.get('UNSPLASH_SECRET', None)
    redirect_uri = ""
    code = ""

    auth = Auth(client_id, client_secret, redirect_uri, code=code)
    api = Api(auth)

    photo_worker = Photo(api=api)

    unsplash_requests = 0

    # get env variable API key
    azure_key = os.environ.get('AZURE_KEY', None)

    azure_requests = 0

    orig_tags, orig_captions = azureAnalysis(orig_photo_url, azure_key)

    write_picture_info(results_file, 'Original Photo:', orig_photo_url, orig_tags, orig_captions)

    search_terms = keyworder.get_search_terms(orig_tags, text)

    tagged_photos = {} # a dict which maps the url where we can find a photo to the tags of that photo
    for term in search_terms:
        download_urls = unsplashRequest(term, api, photo_worker)
        unsplash_requests += 11
        for i, url in enumerate(download_urls):
            try:
                tags, captions = azureAnalysis(url, azure_key)
                tagged_photos[url] = tags

                heading = 'Search term: %s\tResult #%d' %(term, i)
                write_picture_info(results_file, heading, url, tags, captions)
            except KeyError:
                print('KeyError with image. Image is probably "not accessible." Moving on to next one.')
            azure_requests += 1
        if unsplash_requests > 80 or azure_requests > 250:
            break

    scores = {}
    for url, tags in tagged_photos.items():
        sm = SequenceMatcher(orig_tags, tags)
        scores[url] = sm.ratio()

    best_url = max(scores, key=scores.get)
    urllib.request.urlretrieve(best_url, 'BEST.jpeg')

    best_tags = tagged_photos[best_url]
    write_picture_info(results_file, 'BEST PHOTO:', best_url, best_tags, None)

    results_file.close()


if __name__ == '__main__':
    orig_photo_url = 'http://sheepmountain.com/wp-content/uploads/2016/01/20150131-DSC_0640-3-1500x700.jpg'
    text = open('goat_mountain.output').read()
    main(orig_photo_url, text)