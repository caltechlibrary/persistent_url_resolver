#!/usr/bin/env python3
import sys
import requests
import boto3
from progressbar import progressbar
from datetime import datetime
import csv, os, argparse
from py_dataset import dataset
from subprocess import run, Popen, PIPE

def usage():
    app_name = os.path.basename(sys.argv[0])
    print(f'''
USAGE {app_name} -host HOSTNAME  -purr_sql PURR_SQL_SCRIPT

This will update all resolver URLS for given host
and purr SQL script.

First parameter is connection string (userid@hostname)
and second is the path to the purr SQL script on the
remote server.

Example:

  {app_name} -host datawork@oralhistories.library.caltech.edu \
          -purr_sql ./purr_caltechoh.sql

''')
    sys.exit(1)

def purr_eprints(connect_string, sql_script_name):
    """purr_eprints - contact the MySQL on a remote EPrints server and
    retrieve the assigned resolver URL and eprint record URL.
    
     EPrints' SQL:  
    
    "SELECT id_number, eprintid FROM eprint WHERE eprint_status = 'archive'"
    
    Write out "purr_${hostname}.csv" with resolver URL and EPrints URL.
    
    Example SQL script "purr_${hostname}.csv"
    
    -- 
    -- Run this script from remote system using the --batch option to generate
    -- a Tab delimited version of output. Use tr to convert tab to comma.
    --
    USE ${DB_NAME_HERE};
    SELECT id_number, 
      CONCAT('${URL_PREFIX_HERE','/', eprintid) 
      FROM eprint WHERE eprint_status = 'archive';
    """
    remote_cmd = f"""mysql --batch < '{sql_script_name}' """
    cmd = ["ssh", connect_string, remote_cmd]
    with Popen(cmd, stdout=PIPE, encoding="utf-8") as proc:
        src = proc.stdout.read().replace("\t", ",")
        return list(csv.reader(src.splitlines(), delimiter=","))


def get_datacite_dois(client_ids, links):
    """Get DataCite DOIs and URLs for specific client IDs"""
    new_links = {}
    base_url = "https://api.datacite.org/dois?page[cursor]=1&page[size]=500&client-id="
    for client in client_ids:
        print("Collecting DOIs for ", client)
        url = base_url + client
        next_link = url
        meta = requests.get(next_link).json()["meta"]
        for j in progressbar(range(meta["totalPages"])):
            r = requests.get(next_link)
            data = r.json()
            for doi in data["data"]:
                if doi["id"] not in links:
                    new_links[doi["id"]] = doi["attributes"]["url"]
                upper = doi["id"].upper()
                if upper not in links:
                    new_links[upper] = doi["attributes"]["url"]
            if "next" in data["links"]:
                next_link = data["links"]["next"]
            else:
                next_link = None
    return new_links


def make_s3_record(s3, bucket, resolver, url):
    """Make S3 entry for a redirect"""
    s3_object = s3.Object(bucket_name=bucket, key=resolver)
    response = s3_object.put(WebsiteRedirectLocation=url, ACL="public-read")
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("Error: ", response)


def links_differ(link1, link2):
    """Return whether two links are different"""
    differ = True
    if link1 == link2:
        differ = False
    # Handle when url had training slash
    if link1[0:-1] == link2:
        differ = False
    if link2[0:-1] == link1:
        differ = False
    return differ


def save_history(existing, url, get):
    """We save the history if anything has changed"""
    save = False
    if links_differ(url, existing["expected-url"]):
        save = True
    if get.status_code != existing["code"]:
        save = True
    if links_differ(get.url, existing["url"]):
        save = True
    return save


def make_link_history(collection, resolver, url, note):
    """Make an entry in our link history collection"""
    now = datetime.today().isoformat()
    # Run checks on both resoler and final URL
    try :
        target = requests.get(url)
    except requests.exceptions.ConnectionError:
        target = requests.Response()
        target.status_code = 404
        target.url = ''
    if target.status_code != 200:
        print(f"Target URL {url} returns Error status code {target.status_code}")
    if links_differ(target.url, url):
        print(f"Target URL '{url}' redirects to '{target.url}'")
    try :
        get = requests.get(f"https://resolver.library.caltech.edu/{resolver}")
    except requests.exceptions.ConnectionError:
        get = requests.Response()
        get.status_code = 404 
        get.url = ''
    if links_differ(get.url, url):
        print(f"Mismatch between expected url '{url}' and actual '{get.url}'")
    if get.status_code != 200:
        print(f"Resolver URL ({resolver}) '{get.url}' returns Error status code {get.status_code}")
    entry = {
        "expected-url": url,
        "url": get.url,
        "modified": now,
        "code": get.status_code,
        "note": note,
    }
    # If existing, push into history
    if dataset.has_key(collection, resolver):
        existing, err = dataset.read(collection, resolver)
        if err != "":
            print(err)
            exit()
        if save_history(existing, url, get):
            past_history = existing.pop("history")
            past_history.append(existing)
            entry["history"] = past_history
            if not dataset.update(collection, resolver, entry):
                print(dataset.error_message())
                exit()
    else:
        entry["history"] = []
        if not dataset.create(collection, resolver, entry):
            print(dataset.error_message())
            exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the CODA URL Resolver")
    parser.add_argument(
        "-update", action="store_true", help="Update ALL (not just new) resolver links"
    )
    parser.add_argument(
        "-dois", action="store_true", help="Get resolver links from DataCite"
    )
    parser.add_argument(
        "-skip_eprints", action="store_true", help="Get resolver links from DataCite"
    )
    parser.add_argument(
        "-host", help="Username and hostname, datawork@machine.example.edu"
    )
    parser.add_argument(
        "-purr_sql", help="Path to purr sql generate"
    )

    args = parser.parse_args()

    # S3 Setup
    session = boto3.Session(profile_name="resolver")
    current_region = session.region_name
    bucket = "resolver.library.caltech.edu"
    s3 = session.resource("s3")

    collection = "link_history.ds"
    if os.path.isdir(collection) == False:
        make_s3_record(s3, bucket, "index.html", "https://libguides.caltech.edu/CODA")
        if not dataset.init(collection):
            print("Dataset failed to init collection")
            exit()

    # Get the links that already exist
    links = dataset.keys(collection)
    if args.update:
        # Everything will get updated
        links = []

    # Get DOI links
    if args.dois:
        client_ids = [
            "tind.caltech",
            "caltech.library",
            "caltech.ipacdoi",
            "caltech.micropub"
        ]
        new_links = get_datacite_dois(client_ids, links)
        for l in progressbar(new_links):
            print(l)
            if l not in links:
                make_s3_record(s3, bucket, l, new_links[l])
                make_link_history(collection, l, new_links[l], "From DataCite")

    eprints = True
    if args.skip_eprints:
        eprints = False

    if eprints:
        # Get Eprints links
        if (args.host == '') or (args.purr_sql == ''):
            usage()
        repos = [(args.host, args.purr_sql)]
        for r in repos:
            print(r[1])
            eprints_links = purr_eprints(r[0], r[1])
            for l in eprints_links:#progressbar(eprints_links, redirect_stdout=True):
                idv = l[0]
                url = l[1]
                # Skip header
                if idv != "resolver_id":
                    #if idv not in links:
                    make_s3_record(s3, bucket, idv, url)
                    make_link_history(collection, idv, url, f"From {r[1]}")
