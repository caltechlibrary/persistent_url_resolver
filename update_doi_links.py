import requests
from progressbar import progressbar
from datacite import DataCiteRESTClient

def get_datacite_dois(client_ids):
    """Get DataCite DOIs and URLs for specific client IDs"""
    links = {}
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
                item_url = doi["attributes"]["url"]
                if 'http://resolver.caltech.edu' in item_url:
                    links[doi["id"]] = item_url
            if "next" in data["links"]:
                next_link = data["links"]["next"]
            else:
                next_link = None
    return links


if __name__ == "__main__":
    prefix='10.26206'

    #DataCite Setup
    d = DataCiteRESTClient(
    username='CALTECH.LIBRARY',
    password='',
    prefix=prefix,
    )

    client_ids = ["caltech.library"]
    links = get_datacite_dois(client_ids)
    for l in progressbar(links):
        if l.split('/')[0] == prefix:
            print(l)
            new_link = links[l].replace('http://','https://')
            d.update_url(l,new_link)
