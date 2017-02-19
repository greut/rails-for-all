#!/bin/sh
exec 2>&1
export HOME=/var/lib/postgres
exec chpst -u postgres -U postgres \
    /usr/lib/postgresql/9.6/bin/postgres \
    -D /etc/postgresql/9.6/main/
