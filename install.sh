#!/bin/sh

set -xe

DEBIAN_FRONTEND=noninteractive

MYSQL_VERSION=5.7
POSTGRES_VERSION=9.6
TINI_VERSION=0.13.2
RUBY_VERSION=2.4
NODEJS_VERSION=7.x

# All the packages.
apt-get update -q
apt-get upgrade -q -y
apt-get install -q -y \
    acl \
    apt-transport-https \
    autoconf \
    build-essential \
    ca-certificates \
    cron \
    curl \
    fontconfig \
    git \
    imagemagick \
    libcurl4-gnutls-dev \
    libgdbm-dev \
    libmagickwand-dev \
    libmysqlclient-dev \
    libncurses5-dev \
    libreadline6-dev \
    libsass-dev \
    libsqlite3-dev \
    libtool-bin \
    libxml2-dev \
    libxslt1-dev \
    libyaml-dev \
    lsof \
    man \
    mysql-client-${MYSQL_VERSION} \
    nano \
    nginx \
    openssh-server \
    psmisc \
    pwgen \
    python3-pip \
    python3-venv \
    runit \
    software-properties-common \
    sqlite3 \
    ssmtp \
    sudo \
    syslog-ng \
    unzip \
    vim \
    wget


# Add Tini (reaping problem)
wget https://github.com/krallin/tini/releases/download/v${TINI_VERSION}/tini --quiet -O /tini
sig=`sha256sum /tini | cut -d " " -f1`
expected=790c9eb6e8a382fdcb1d451f77328f1fac122268fa6f735d2a9f1b1670ad74e3
if [ "$expected" = "$sig" ]; then
    chmod +x /tini
else
    echo "tini checksum doesn't match ours."
    exit 1
fi

# Ruby NG
apt-add-repository ppa:brightbox/ruby-ng

# NodeSource Apt Repository
# https://deb.nodesource.com/setup_7.x
echo "deb https://deb.nodesource.com/node_${NODEJS_VERSION} yakkety main" \
  > /etc/apt/sources.list.d/nodesource.list
wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key \
  | apt-key add -

# PostgreSQL Apt Repository
# https://www.postgresql.org/download/linux/ubuntu/
#
# (yakkety is not yet supported, so xenial)
echo "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main" \
  > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  | apt-key add -

# Installation of external and “experimental” packages
apt-get update
apt-get install -q -y \
    libpq-dev \
    nodejs \
    postgresql-client-${POSTGRES_VERSION} \
    ruby${RUBY_VERSION} \
    ruby${RUBY_VERSION}-dev \
    ruby-switch

# Post Installation
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Ruby
ruby-switch --set ruby$RUBY_VERSION
echo "gem: --no-document" > /etc/gemrc

# OpenSSH Server
#
# * Disable password authentication
# * Disallow TCP forwarding
# * Delete any configured host keys (boot.sh)
#
f=/etc/ssh/sshd_config
mkdir /var/run/sshd
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' $f
sed -i 's/^AllowTcpForwarding yes/AllowTcpForwarding no/' $f
rm -v /etc/ssh/ssh_host_*

# Locale
for l in "fr_CH" "de_CH" "it_CH" "en_US";do
    locale-gen $l
    locale-gen $l.UTF-8;
done
update-locale LANG=fr_CH.UTF-8 LC_MESSAGES=POSIX

# Syslog
#
# * Output all the things to stdout!
#
f=/etc/syslog-ng/syslog-ng.conf
sed -i 's/system()/#system()/' $f
sed -i 's/^\(# The root\)/# Stdout\/Stderr\n\n\1/' $f
sed -i 's/^\(# The root\)/destination d_stdout { pipe("\/dev\/stdout"); };\n\1/' $f
sed -i 's/^\(# The root\)/destination d_stderr { pipe("\/dev\/stderr"); };\n\n\1/' $f
sed -i 's/\(destination\)(d_[^)]*)/\1(d_stdout)/g' $f
sed -i 's/\(filter(f_console);\)\s*destination(d_stdout);/\1/g' $f

# Good umask
f=/etc/login.defs
sed -i 's/^UMASK.*$/UMASK 027/' $f

## Nginx
f=/etc/nginx/nginx.conf
rm /etc/nginx/sites-enabled/default \
 && rm -r /var/www/html \
 && sed -i 's/\(worker_processes\) .*;/\1 auto;\ndaemon off;/' $f \
 && sed -i 's/\/var\/log\/nginx\/access.log/\/dev\/stdout/' $f \
 && sed -i 's/\/var\/log\/nginx\/error.log/\/dev\/stdout/' $f
