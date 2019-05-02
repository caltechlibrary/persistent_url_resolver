import requests
import boto3

def get_datacite_dois(client_ids):
    '''Get DataCite DOIs and URLs for specific client IDs'''
    linking = {}
    base_url = 'https://api.datacite.org/dois?client-id='
    for client in client_ids:
        url = base_url + client
        next_link = url
        while next_link != None:
            r = requests.get(next_link)
            data = r.json()
            for doi in data['data']:
                linking[doi['id']] = doi['attributes']['url']
            if 'next' in data['links']:
                next_link = data['links']['next']
            else:
                next_link = None
    return linking

def make_s3_record(s3,bucket,resolver_url,url):
    '''Make S3 entry for a redirect'''
    s3_object = s3.Object(
    bucket_name=bucket, key=resolver)
    response = s3_object.put()
    print(response)

if __name__ == "__main__":
    client_ids = ['caltech.micropub']
    #['tind.cal','caltech.library','caltech.ipacdoi','caltech.micropub','caltech.hte']
    #linking = get_datacite_dois(client_ids)
    session = boto3.Session(profile_name='resolver')
    current_region = session.region_name
    bucket = 'resolver.library.caltech.edu'
    s3 = session.client('s3')
    resolver = 'test'
    url = 'testurl'
    make_s3_record(s3,bucket,resolver,url)
    #result = s3.get_bucket_website(bucket)
    #print(result)
