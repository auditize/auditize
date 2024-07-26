#!/bin/bash

set -e
set -x

# We set the purge expired logs task to run every minute because
# it's easier to deal with in a demo/test environment.

declare | grep ^AUDITIZE_ >  /etc/cron.d/auditize
cat <<EOF >> /etc/cron.d/auditize
* * * * * root /usr/local/bin/python -m auditize purge_expired_logs >> /var/log/auditize.log 2>&1
EOF

exec cron -f & tail -F /var/log/auditize.log
