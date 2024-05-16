#!/bin/bash
set -e
DIR=$( cd $(dirname $0) ; pwd)
cd "$DIR"

./_src/make.py

grep -rl '/online/' build | xargs -n1 perl -pe 's@/online/@/online-dev/@;' -i

rsync -avzHAXx --partial --inplace --delete -c build/ kal@learn.gl:public_html/online-dev/docs/

echo "Uploaded to https://learn.gl/online-dev/docs/"
