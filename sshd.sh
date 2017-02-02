#!/bin/sh
set -xe
exec 2>&1
exec /usr/sbin/sshd -D
