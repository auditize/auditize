#!/bin/bash

set -e
set -x

declare | grep ^AUDITIZE_ >  /etc/cron.d/auditize
cat <<EOF >> /etc/cron.d/auditize
* * * * * root /usr/local/bin/python -m auditize purge_expired_logs >> /etc/cron.d/auditize
EOF

exec cron -f
