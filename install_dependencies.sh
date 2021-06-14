# (1) system setup
sudo apt update -y
sudo apt-get upgrade -y
sudo apt install python3-pip -y
sudo apt install ffmpeg -y
sudo apt install mediainfo -y
sudo apt-get install sox -y
sudo apt -y install fail2ban

# install server management -nginx, supervisor, postgres
sudo apt install nginx -y
sudo apt-get install -y supervisor
sudo apt install postgresql postgresql-contrib -y # looking to decouple this
sudo apt-get install python-psycopg2 -y
sudo apt-get install libpq-dev -y

# (2) prepare task runner and message broker for celery that will handle async tasks
sudo apt-get install -y erlang
sudo apt-get install -y rabbitmq-server

sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server

# s3 backups
sudo apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# (3) python packages - create virtual env - necessary to have supervisor manage gunicorn 
sudo apt install virtualenv -y
pip3 install virtualenv
git clone https://fmcgregor@bitbucket.org/fmcgregor/django_project.git
cd $HOME/django_project
virtualenv --python=python3 env
source env/bin/activate


# (4) setup supervisor to manage gunicorn and celery
# setup supervisor to manage gunicorn
sudo cp confs/gunicorn.conf /etc/supervisor/conf.d/gunicorn.conf
sudo mkdir /var/log/gunicorn

# configure gunicorn supervisor
sudo cp confs/celery.conf /etc/supervisor/conf.d/celery.conf
sudo mkdir /var/log/celery

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status 

# restart to load changes to code
sudo cp confs/nginx.conf /etc/nginx/nginx.conf
sudo service supervisor restart
sudo service nginx restart
sudo supervisorctl restart all

# (5) Configure nginx to read from the socket file that gunicorn is creating
sudo cp confs/django.conf /etc/nginx/sites-enabled/django.conf
sudo nginx -t
sudo service nginx restart
sudo systemctl reload nginx

# (6) Install elastic search
#https://phoenixnap.com/kb/install-elasticsearch-ubuntu
sudo apt-get install openjdk-8-jdk
sudo apt install apt-transport-https
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list

sudo apt update
sudo apt install elasticsearch
sudo systemctl daemon-reload
sudo systemctl enable elasticsearch.service
sudo systemctl start elasticsearch.service