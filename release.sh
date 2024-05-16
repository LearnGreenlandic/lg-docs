#!/bin/bash
set -e
DIR=$( cd $(dirname $0) ; pwd)
cd "$DIR"

./_src/make.py

rsync -avzHAXx --partial --inplace --delete -c build/ kal@learn.gl:public_html/online/docs/

echo "Uploaded to https://learn.gl/online/docs/"
