# Persistent URL Resolver

Resolve existing Persistent URLs in Eprints and Caltech Library DOIs using AWS
S3. At Caltech this is installed and runs on the betawork server.

## Install

We use uv to manage python dependencies. Create a local venv with `uv venv` and then
install dependencies with `uv pip install -r requirements.txt`

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

In order to get https, we need to set up a cloudfront distribution.  First go
to S3 settings under static website hosting and copy the domain name - it will
be something like
"resolver.library.caltech.edu.s3-website-us-west-2.amazonaws.com".
Now go to cloudfront in AWS and create a Web distribution.
Paste the S3 url as Origin Domain Name- do not use the default S3 autocomplete.  
For now allow both HTTP and HTTPS.  All the defaults should be fine.
Note that it may take awhile to deploy your site if you have many objects. 

## Operation

If you need to manually add a resolver link, you can use the `resolver_link.py`
 script. You provide the resolver name, the url, and a message for the log. 
 `python change_resolver_link.py CaltechBOOK:1984.001 https://authors.library.caltech.edu/25061/ "Capitalization"`

The `resolver.py` script automates setting up the resolver.  `python
resolver.py` will find resolver links in Eprints repositories and upload them
to S3. Normally only new links are added, but if you want to update all the
links add the `-update` flag.  This will take many hours. If you want to update
DOI links, add the `-dois` flag.

