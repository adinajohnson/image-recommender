import http.client, urllib.request, urllib.parse, urllib.error, base64, json, os, requests
from unsplash.api import Api
from unsplash.auth import Auth
from unsplash.photo import Photo
import time
import keyworder
import sys


def azureAnalysis(photo_url, subscription_key):
    """
    Does Microsoft Azure (TM) analysis on a photo at a given url.
    :param photo_url: the url of the photo to be analyzed
    :param subscription_key: the key which one uses to access Azure visual analysis services
    :return: tags: the list tags which Azure returns. captions: a dictionary of the caption and confidence which Azure returns
    """

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


def unsplashRequest(search_term, api, photo_worker):
    """
    Gets a list of urls of photos from the Unsplash database.
    :param search_term: the search term to query the database
    :param api: An Unsplash api object from the unsplash library
    :param photo_worker: an unsplash.photo.Photo object
    :return: photo_urls: a list of urls of photos
    """
    # search the unsplash database for the given term
    photos = api.search.photos(search_term, per_page=15)['results']

    photo_urls = []
    for photo in photos:
        # get the download url for one of the photos returned by the search
        url = photo_worker.download(photo.id)['url']
        photo_urls.append(url)

    return photo_urls


def jaccard(A, B):
    """
    Computes the Jaccard index of two sets.
    :param A: one set
    :param B: another set
    :return: the jaccard index.
    """
    A = set(A)
    B = set(B)

    numer = len(A & B) # the length of the intersection of sets A and B
    denom = len(A | B) # the length of the union of sets A and B
    return numer/denom


def write_picture_info(file, heading, url, tags, captions=None):
    """
    Writes some info about a picture to a file, including its url and some of the info from an Azure analysis
    :param file: the file to which you want to write the info
    :param heading: a heading which can give some information about the image
    :param url: the url of the image
    :param tags: the list of the tags returned by Azure
    :param captions: optional. The "captions" dictionary that Azure returns.
    :return:
    """
    # record some data
    file.write(heading + '\n')
    file.write(url)
    file.write('\n')
    file.write(str(tags))
    if captions is not None:
        file.write('\n')
        file.write(str(captions).strip('[{}]'))
    file.write('\n\n')


def recommend(orig_photo_url, text):
    """
    Handles the image recommending.
    :param orig_photo_url: the url where the
    :param text: the context text to look at to rank the tags
    :return:
    """
    # get a file so we can write results into it
    results_file = open('Everest_WierdD_0_01.output', 'w')

    #get unsplash API stuff
    client_id = os.environ.get('UNSPLASH_ID', None)
    client_secret = os.environ.get('UNSPLASH_SECRET', None)
    redirect_uri = ""
    code = ""
    auth = Auth(client_id, client_secret, redirect_uri, code=code)
    api = Api(auth)
    photo_worker = Photo(api=api)

    # get env variable Azure API key
    azure_key = os.environ.get('AZURE_KEY', None)

    # do Azure analysis on the original photo that we want recommendations for, and write the retrieved into to a file
    orig_tags, orig_captions = azureAnalysis(orig_photo_url, azure_key)
    write_picture_info(results_file, 'Original Photo:', orig_photo_url, orig_tags, orig_captions)

    # use those tags and the text provided to get a re-ranking of the importance of tags/search terms
    search_terms = keyworder.get_search_terms(orig_tags, text, results_file)

    tagged_photos = {} # a dict which maps the url where we can find a photo to the tags of that photo

    # iterate through the top 3 search terms and search each one
    for term in search_terms[:5]:
        photo_urls = unsplashRequest(term, api, photo_worker)

        # analyze each of the photos returned
        for i, url in enumerate(photo_urls):
            try:
                # the following line will throw an KeyError if Azure can't use the photo url, which happens often
                tags, captions = azureAnalysis(url, azure_key)
                tagged_photos[url] = tags

                # write information about this photo to a file
                heading = 'Search term: %s\tResult #%d' %(term, i)
                write_picture_info(results_file, heading, url, tags, captions)
            except KeyError:
                print('KeyError with image. Image is probably "not accessible." Moving on to next one.')

    scores = {} # this dict will map photo urls to a similarity score, so that we can find the most similar photo
    for url, tags in tagged_photos.items():
        scores[url] = jaccard(orig_tags, tags)

    # the image we want to recommend is the photo with the highest similarity score
    best_url = max(scores, key=scores.get)
    # save the photo to disk so we can look at it.
    urllib.request.urlretrieve(best_url, 'BEST.jpeg')

    # write information about the best photo to the file.
    best_tags = tagged_photos[best_url]
    write_picture_info(results_file, 'BEST PHOTO:', best_url, best_tags, None)

    results_file.close()


if __name__ == '__main__':
    orig_photo_url = sys.argv[1]
    text_path = sys.argv[2]
    text = open(text_path).read()
    recommend(orig_photo_url, text)