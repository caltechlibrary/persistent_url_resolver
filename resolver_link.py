import requests
import boto3
from progressbar import progressbar
from datetime import datetime
import csv, os, argparse
from py_dataset import dataset
from subprocess import run, Popen, PIPE
import resolver

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update a link in the CODA URL Resolver to a specific new link"
    )
    parser.add_argument("id", help="Resolver ID for content")
    parser.add_argument("url", help="New URL for content")
    parser.add_argument(
        "message",
        help="Message explaining the change, will be added to resolver history",
    )

    args = parser.parse_args()

    # S3 Setup
    session = boto3.Session(profile_name="resolver")
    current_region = session.region_name
    bucket = "resolver.library.caltech.edu"
    s3 = session.resource("s3")

    collection = "link_history.ds"

    resolver.make_s3_record(s3, bucket, args.id, args.url)
    resolver.make_link_history(collection, args.id, args.url, args.message)
