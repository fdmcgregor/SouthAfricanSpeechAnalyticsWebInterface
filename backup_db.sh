#!/bin/bash
set -e
set -o pipefail
set -u

echo "Info [`date`]: starting db backup" >> $HOME/db.tmp

$HOME/django_project/env/bin/python3 $HOME/django_project/manage.py dumpdata | gzip > $HOME/django_project/db.json.gz
echo "Info [`date`]: done data dump" >> $HOME/db.tmp
/usr/local/bin/aws s3 cp $HOME/django_project/db.json.gz s3://saigen-stt-frontend/db.dsac.json.gz
echo "Info [`date`]: done data copying to s3" >> $HOME/db.tmp