<br />
<p align="center">
  <a href="https://github.com/pieter129/KaldiSpokenTermDetectionWrapper">
    <img src="images/logo.png" alt="Logo" width="160" height="80">
  </a>
  <h1 align="center">Web interface</h1>
  <p align="center">
    Web interface for South African speech analytics. 
    <br />
    Web app built with django.
    <br />
    <br />
  </p>
</p>

## Table of Contents

* [Starting up]
* [Getting your server production ready]
* [Code architecture overview]
* [License](#license)
* [References](#references)


## About The Project

**Version**: 0.1
**Date**: 2021-06-14 

This repository was developed and released by [Saigen (Pty) Ltd](https://www.saigen.co.za/) as part of the 
Speech Analytics for the South African Languages (SASAL) project carried out 
with the support of the South Africa Department of Sports, Arts and Culture 
(2018-06-01 to 2021-07-31).


# Starting up
1. Start a new ec2 instance on AWS running Ubuntu 18.04
2. Open port 8000 for development and 80 for testing nginx.
3. `git clone https://github.com/fdmcgregor/SouthAfricanSpeechAnalyticsWebInterface.git`
4. Run `install_dependencies.sh`
5. Create a `.env` file containing private keys with the following: 

    - AWS credentials to host the media files on s3. Add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`. It is also useful to set your AWS command line interface at this stage `aws configure`. Copy the static files to your s3 bucket as we serve it form there.

    - Set up an emailing address and emailing client with sendgrid mailing server. Get an api key (it's free for up to 100 emails a day) and save as `SENDGRID_API_KEY`. Save sender email address as `EMAIL_USER`.

    - Set up a postgres database (if you are just getting started you can use sqlite by changing `LOCAL_DB` to True in `settings.py` and you can skip this part).

    Create a database (`RDS_NAME`) and user (`RDS_USER`) passdword (`RDS_PASS`):
    `sudo -u postgres psql`
    ```
    >>> CREATE USER `RDS_USER` WITH ENCRYPTED PASSWORD `RDS_PASS`;
    >>> CREATE DATABASE `RDS_NAME`;
    ```
    And add `RDS_USER`,`RDS_NAME`,`RDS_PASS`,`RDS_HOST` with `RDS_HOST="localhost"` as we are running postgres database server locally.

    Then from the console run:
    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```

    - Set up your backend API service and include then variables `LAMBDA_URL` and `LAMBDA_API_KEY` in `.env`.

    - Enable elastic search to index all the files in the database `python3 manage.py search_index --rebuild`.

4. Check that the server runs in development mode: 

* start server on open port 8000: `python3 manage.py runserver 0.0.0.0:8000`
* start task runner in debug mode: `celery -A speech_analytics_platform worker -l info`

Navigate to `http://<your public ip>:8000` and check that the webapp runs. This setup is useful for development and should not be used in production.

# Getting your server production ready

1. For production use `supervisor` with programs specified in `gunicorn.conf` and `celery.conf`. This should have been started with `install_dependencies.sh` check the status of these tasks with `sudo supervisorctl status`. 
2. Check whether nginx is serving on port 80 - visit `http://<your public ip>` and check that the web app is running.
3. For a SSL certificate with certbot, a domain name is required. You can purchase and use AWS Route 53 to as a name server. Then expose port 443 for HTTPS traffic. 

```
sudo add-apt-repository ppa:certbot/certbot
sudo apt install python-certbot-nginx -y
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

Change the server name in `confs/nginx.conf` to the the domain name you have purchased and run 
```
sudo certbot -nginx
sudo systemctl restart nginx
```
for changes to take effect. The website should now accept secure and encrypted SSL requests with the new SSL certificate.  

The SSL certificate needs to be renewed every 3 months. We set up a cronjob to renew it automatically. Create a new crojob with
`sudo crontab -e` and enter
```
30 4 1 * * sudo /usr/bin/certbot renew --quiet
```
to renew at 04:30 AM ont the 1st of every month.

### Create new admin user from command line
`python3 manage.py createsuperuser`


### Production server
The `supervisor` program runs 2 process specified in which will ensure that they are always on and will restart them if the processes break or the server is restarted. It runs `gunicorn` to serve the website and `celery` which is the taskrunner that handles long processes like sending emails and sending out speech recogntion jobs. 

Make sure the supervisor is running with `sudo supervisorctl status` or restart a service once changes have been made with `sudo supervisorctl restart all`. It is also possible to restart individual services `sudo supervisorctl restart guni:gunicorn` or `sudo supervisorctl restart decoding_app_celery`. 

### Resetting users that have been shut out 
Ip addresses will be allowed 5 failed attempts before blocking the ip. It will reset in 2 hours or if urgent one can reset django-axes:
`python3 manage.py axes_reset`

### Interacting with the database and new users
Log into admin account and navigate to admin page <your-url>/manage/ where you can create users and interact with the database.


# Code architecture overview 
Inside `django_project/speech_analytics_platform` lie the project files and you may have to interact with `settings.py` to configure how the app is served.
##  

There are 3 apps `decoding_app`, `users` and `search`. 
1. Users manages users and 
2. Decoding app handles recording transcriptions and saves them as posts
3. Search handles building search queries with elastic search 

In each app: 
##  
Most work is done `in views.py` and start here. This serves the page to a client’s response, it sends some “context” which is just a dictionary, to the “templates” which are html but can be populated with the context that is sent to it. 
##  
Then `models.py` is where django defines a face for interactions with a database. 
##  
In the templates folder the html “templates” are stored, if you just need to make a cosmetic change start here

### In decoding app
`decode_service.py` manages sending API requests 
##  
`tasks.py` generally for other asynchronous tasks 
##  
`services.py` is where for non user request/response related services 

# Log files
### Gunicorn (manages requests and client server interaction - web app related problems)
`/var/log/gunicorn/gunicorn.err.log` 
###  
`/var/log/gunicorn/gunicorn.out.log`

### Celery (task runner that asynchronously sends API requests- decoding related problems)
`/var/log/celery/celery-worker.err.log` 
###  
`/var/log/celery/celery-worker.out.log`

### Nginx
`/var/log/nginx/error.log` 
###  

Edit 
###  
`/etc/nginx/nginx.conf`
###  
`/etc/nginx/sites-enabled/django.conf `
###  

For changes to take effect: 
###  
`sudo systemctl restart nginx `
###  

### Database related changes 
###  
`python3 manage.py makemigrations `
###  
`python3 manage.py migrate` 
###  
    
## License

Distributed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/legalcode).
See `LICENSE` for more information.
    
## References
[1] (https://kaldi-asr.org/doc/kws.html)  
[2] (https://github.com/pieter129/KaldiSpokenTermDetectionWrapper) 
