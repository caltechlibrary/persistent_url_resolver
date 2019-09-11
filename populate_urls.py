import requests
import boto3
from progressbar import progressbar
from datetime import datetime
import csv,os
from py_dataset import dataset
from subprocess import run, Popen, PIPE

#
# purr_eprints - contact the MySQL on a remote EPrints server and
# retrieve the assigned resolver URL and eprint record URL.
#
# EPrints' SQL:  
#
#  "SELECT id_number, eprintid FROM eprint WHERE eprint_status = 'archive'"
#
# Write out "purr_${hostname}.csv" with resolver URL and EPrints URL.
# 
# Example SQL script "purr_${hostname}.csv"
#
# -- 
# -- Run this script from remote system using the --batch option to generate
# -- a Tab delimited version of output. Use tr to convert tab to comma.
# --
# USE ${DB_NAME_HERE};
# SELECT id_number, 
#     CONCAT('${URL_PREFIX_HERE','/', eprintid) 
#     FROM eprint WHERE eprint_status = 'archive';
#
def purr_eprints(connect_string, sql_script_name):
    remote_cmd = f'''mysql --batch < '{sql_script_name}' '''
    cmd = [
            "ssh",
            connect_string,
            remote_cmd
          ]
    with Popen(cmd, stdout = PIPE, encoding = 'utf-8') as proc:
        src = proc.stdout.read().replace("\t", ",")
        print(src)
        #with open(output_csv, 'w') as fp:
        #    fp.write(src)
        #t = src.split('\n')
        #print(f'Wrote {len(t)} lines to {output_csv}')

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

def make_link_history(collection,resolver,url,note):
    '''Make an entry in our link history collection'''
    now = datetime.today().isoformat()
    #Run link check
    get = requests.get('https://ddlgr1hc96u88.cloudfront.net/'+resolver)
    if get.url != url:
        print(f"Mismatch between expected url {url} and actual {get.url}")
    entry = {'expected-url':url,'url':get.url,'modified':now,
            'code':get.status_code,'note':note}
    #If existing, push into history
    if dataset.has_key(collection,resolver):
        existing,err = dataset.read(collection,resolver)
        if err != '':
            print(err)
            exit()
        past_history = existing.pop('history')
        past_history.append(existing)
        entry['history'] = past_history
        err = dataset.update(collection,resolver,entry)
    else:
        entry['history'] = []
        err = dataset.create(collection,resolver,entry)
        if err != '':
            print(err)
            exit()

if __name__ == "__main__":
    collection = 'link_history.ds'
    if os.path.isdir(collection) == False:
        ok = dataset.init(collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()
    #Get the links that already exist
    links = dataset.keys(collection)
    
    #S3 Setup
    session = boto3.Session(profile_name='resolver')
    current_region = session.region_name
    bucket = 'resolver.library.caltech.edu'
    s3 = session.resource('s3')

    #Get DOI links
    client_ids =['caltech.ipacdoi']
            #['tind.caltech','caltech.library','caltech.ipacdoi','caltech.micropub','caltech.hte']
    new_links = get_datacite_dois(client_ids,links)
    for l in progressbar(new_links):
        make_s3_record(s3,bucket,l,new_links[l])
        make_link_history(collection,l,new_links[l],'From DataCite')

    #Get Eprints links
    repos = [('datawork@authors.library.caltech.edu','./purr_authors.sql')]
    for r in repos:
        purr_eprints(r[0],r[1])

