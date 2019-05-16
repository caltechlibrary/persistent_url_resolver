# Persistent URL Resolver

Resolve existing Persistent URLs in Eprints and Caltech Library DOIs using AWS
S3

## Setup

Create a S3 bucket using the AWS console, say resolver.library.caltech.edu.
You can turn on logging if you like.  For now turn off all public access
restrictions (we don't care if people can read bucket contents).  Then go to
bucket properties and turn on static website hosting (use index.html as the
document root and error.html as the error location).  
Then under permissions add public access for "List objects".

Go to AWS IAM and select policies.  Create a new policy that allows S3 access
to only the resolver.library.caltech.edu bucket and any object.  
Set up a user in AWS AIM (I created a new user "resolver"), and provide it only
programmatic access (no need for it to have a password).  Select "Attach
existing policies dierectly", and select the policy you just created. Create
the user and you'll get credentials.  Edit ~/.aws/credentials and add

    [resolver]   
    aws_secret_access_key = 
    aws_access_key_id =   

resolver is the profile we'll use to hold these credentials.  You should have
in ~/.aws/config

[default]
region = us-west-2

or whatever AWS region you're using.  

Copy error.html, logos, and css.css to the S3 bucket.

Type `python make_index.py` to generate an index file.

Type `python populate_urls.py` to generate DOI resolver links

In order to get https, we need to set up a cloudfront distribution.  First go
to S3 settings under static website hosting and copy the domain name - it will
be something like
"resolver.library.caltech.edu.s3-website-us-west-2.amazonaws.com".
Now go to cloudfront in AWS and create a Web distribution.
Paste the S3 url as Origin Domain Name- do not use the default S3 autocomplete.  
For now allow both HTTP and HTTPS.  All the defaults should be fine.
Note that it will take awhile to deploy your site because there are so many objects. 

