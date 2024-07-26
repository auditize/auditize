#!/bin/bash

set -e
set -x

declare | grep ^AUDITIZE_ >  /etc/cron.d/auditize
cat <<EOF >> /etc/cron.d/auditize
* * * * * root /usr/local/bin/python -m auditize purge_expired_logs >> /var/log/auditize.log 2>&1
EOF

: > /var/log/auditize.log
exec cron -f & tail -f /var/log/auditize.log
