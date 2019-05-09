import requests
import boto3
from progressbar import progressbar
import csv,os

def get_datacite_dois(client_ids,links):
    '''Get DataCite DOIs and URLs for specific client IDs'''
    new_links = {}
    base_url = 'https://api.datacite.org/dois?page[cursor]=1&page[size]=500&client-id='
    for client in client_ids:
        print('Collecting DOIs for ', client)
        url = base_url + client
        next_link = url
        meta = requests.get(next_link).json()['meta']
        for j in progressbar(range(meta['totalPages'])):
            r = requests.get(next_link)
            data = r.json()
            for doi in data['data']:
                if doi['id'] not in links:
                    new_links[doi['id']] = doi['attributes']['url']
                upper = doi['id'].upper()
                if upper not in links:
                    new_links[upper] = doi['attributes']['url']
            if 'next' in data['links']:
                next_link = data['links']['next']
            else:
                next_link = None
    return new_links

def make_s3_record(s3,bucket,resolver,url):
    '''Make S3 entry for a redirect'''
    s3_object = s3.Object(
    bucket_name=bucket, key=resolver)
    response = s3_object.put(WebsiteRedirectLocation=url,ACL='public-read')
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Error: ',response)

if __name__ == "__main__":
    #Local csv copy of links
    link_file = 'resolver_links.csv'
    links = {}
    available = os.path.isfile(link_file)
    #If we have an existing file
    if available == True:
        reader=csv.reader(open(link_file))
        for row in reader:
            links[row[0]] = row[1]
    
    #Get DOI links
    client_ids =\
    ['tind.caltech','caltech.library','caltech.ipacdoi','caltech.micropub','caltech.hte']
    new_links = get_datacite_dois(client_ids,links)
    
    #Upload to S3
    session = boto3.Session(profile_name='resolver')
    current_region = session.region_name
    bucket = 'resolver.library.caltech.edu'
    s3 = session.resource('s3')
    print("Creating new links in S3")
    for l in progressbar(new_links):
        make_s3_record(s3,bucket,l,new_links[l])

    #Save links so we don't re-create them next time
    links = {**links,**new_links}
    with open(link_file,'w') as f:
        w = csv.writer(f)
        w.writerows(links.items())
