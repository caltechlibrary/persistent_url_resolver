import boto3

def make_s3_record(s3,bucket,resolver,url):
    '''Make S3 entry for a redirect'''
    s3_object = s3.Object(
    bucket_name=bucket, key=resolver)
    response = s3_object.put(WebsiteRedirectLocation=url,ACL='public-read')
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print('Error: ',response)

if __name__ == "__main__":
    
    session = boto3.Session(profile_name='resolver')
    current_region = session.region_name
    bucket = 'resolver.library.caltech.edu'
    s3 = session.resource('s3')
    make_s3_record(s3,bucket,'index.html','https://libguides.caltech.edu/CODA')

