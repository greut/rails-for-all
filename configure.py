#!/usr/bin/env python3
"""
Create tons of users and set up their Ruby on Rails installation.

/home/user
          /.env                  # runit
          /.envfile              # systemd
          /.profile
          /.ssh/authorized_keys
          /config/nginx.conf
                 /puma.rb
          /logs
          /www/app/...
"""

import multiprocessing
import os
import logging
import pwd
import random
import subprocess
import sys
import tempfile

from collections import namedtuple

User = namedtuple('User', 'name ssh_keys')

USERS = (User('yoan', (
    'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDVHwpNj+Fdh2zfi+SXnJrOFqC0Z30VV8ta5aaXUCPvas9sDDDZyEXRdwdbydUkLyXd9a/6eHD5I//JmZ0FKT4zRqtB5Xwu+gjMGVtMXc+qsAPIMPsrYGRYHL14m6prQB4myjTJZmGB5Auf9N6rYFOE01bkoZfU3wYpwZP0t2vCAYJwoN20d5H87i0KB6SngamdgIMXH+h7lJcbBGZBxGTL4r0U1SqLTkTGCZ/+7JYQJWNAZKZtMvCyx7KKI03ZR0+SjFSMIurtS8tiVHyAgZ2luyKtH6NlR6O7RDZr0aeONnbDIDHnoaOxVSlTDxHcTXfFDhZhkCTiHUUyr2eseIpH',
)), User('david', (
    'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCYNRTPsKPGniLSzrzhar2N5b90+At1ejBzoRQP3orxcBdRkcNlFdGVL1fk4nYx1GXZNUT9P0Z+jiQjXAk2B/otIEzsBZ+JrkviplWAYZ7qYAZUlTh9o6PdechQlxtAZO4Tys6k0K15GLtZboK7KHJOme5tEszRGGDcFsQRR7QUUM7g39dckUlrfNxkeU196Vo+ZKJ2sDGCc0Pbrm4hCTL/1UzDTVZs7nV0kpnpOXNXKdjGtkwEc03+kcRPs9eb1KKiKxFdHxjc+F56kklF54s/cY8TTyw79SFDRD3/Hc36ldhxGrgxoSKFhVIWyF3mA+n5E87L8H0fsh3MLb1BlIgCMIE82Va9o60a5a9a/Aba+odaMmB/NBO3uD6TX7Ny1Cq61vXa8jnW07/aSYFdPy4r/Y4xW7eovuldRHpdGZub7hwkoUpKc7Iechgcqf+u2JFsfovpGNPBTclVqrBpUJ66y54Gj5SHhgOPRJoMgMN/PNTdAGyZVGDWbGWT5OuVWFF4Q4y/hOJGQSbGaq68Kft6IzLRF0owQctKahwJ1JZEVv3iSLI+NodfdZPxgBqSkZDCZNs6BK2HoPqIjmR5ECkT2ePWAT54cwwlu6DoyymytOTVyCBTQreuDo/zd9Id9fPfAWwrhCs8qYZ7Vgd3Cg97v+M55Vah2vI9HEmVN/Lpzw==',
    'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpcwue83WhRX49KkdKP3YfkigBiFaLaQjwmEfHy2RbS2ub9GOPCxX9k0vK2lUm0hTg8iFRJIKla/dsJ1H2fH2hMfqnJ0d5MRIA6uaHVu4huNtNkFAGNy5C2SgYhENqp49iUSs0D3DoEq72n2e9cqGlxWbq3KBHcb6GJY/Z5Z8vRvdzM8PUMAlTQj2N2Q0vi+RtryHIj7zr2fwlwAlex0A+NtshT9+80EHJZS2aizOIHeF3zKkFSJ1+6ttEBj0hTN6Alzk9+h0F0obgt1LYGkYohhkcQuQ0k0tb6fVgsymlo1vopIBzUGXCXtygCpVaFe6W3MZnoIv4lCceNTzRn+m5'
)), User('raphael', (
    'ssh-dss AAAAB3NzaC1kc3MAAACBAOzL/oLzDj3wRYhMl+EAv7vExo/Ss4Qk5RAXBfwnJVu1Nm8d1h/TY4uaxDlbBoKDitqe4i5Qqt8NTpl576qCPyrnZqfjDQAKsVtSt+Vv0Gf5OqUE+MFr89EWa/Y5fh0cOe7etPZ8PjrRJiicZHcKMLcXakLedGaL2MMsN9zTKnDDAAAAFQCh+kmfSr+CDHe9Q07Bm1iS1bizRwAAAIBK04rSeNxOmTOOBzWDQz0Kk5I6dTrApXwc+4Alj9XjjKHcV1HFwmFbOm2eQFU0pTOcNo7WhW4zvI6O9shLBgW2CVmrfNOXrR/GORlK/ZbMFFpoQMsuOo/PDb8piV8G3bgHO1+N3gLlfMq+GG+ceBo0jBhjQh9XLe3HvWKkvEy9vQAAAIEA4O05TWpIZTiaihPYiZ1ieTklaF6cWftgp/rXumaat8q4nC6lhi4h5LSP/x7N0zNLj7WVFkzhoa+ESwQKBIRQkLj6/2XPATTEs2Lg2wMbFasvDvUo0PJMZADd2p4OuVXQ913qXzQgPQwJ5Q+n2PQkLRWH+eNmxh8O8b2ToTbTKi8=',
)))
HOSTNAME = "capistrano"
POSTGRES_HOST = "localhost"

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def pwgen(length=64):
    """Generate a secure password."""
    proc = subprocess.Popen(
        ["pwgen", "--secure", "{}".format(length), "1"],
        stdout=subprocess.PIPE)
    return proc.communicate()[0].decode().strip()


def create_user(user, password):
    logger.info('create user %s', user.name)
    subprocess.check_call(
        ["useradd", user.name, "--create-home", "--shell", "/bin/bash"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)

    proc = subprocess.Popen(
        ["chpasswd", ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    proc.communicate("{}:{}".format(user.name, password).encode("utf-8"))


def init_user(user, environ):
    logger.info('init user %s', user.name)
    username = user.name
    p = pwd.getpwnam(username)
    uid, gid = p.pw_uid, p.pw_gid
    homedir = p.pw_dir

    # os
    os.initgroups(username, gid)
    os.setgid(gid)
    os.setuid(uid)
    os.umask(0o027)
    os.chdir(homedir)

    # env
    os.environ["USER"] = username
    os.environ["HOME"] = homedir
    os.environ["UID"] = str(uid)
    os.environ["GEM_HOME"] = "{}/{}".format(homedir, environ["GEM_HOME"])
    os.environ["BUNDLE_PATH"] = os.environ["GEM_HOME"]
    os.environ["PATH"] = "{}:{}/bin".format(os.environ["PATH"],
                                            os.environ["GEM_HOME"])

    environ["HOME"] = homedir
    environ["PATH"] = os.environ["PATH"]
    environ["GEM_HOME"] = os.environ["GEM_HOME"]
    environ["BUNDLE_PATH"] = os.environ["BUNDLE_PATH"]

    # update .profile and env directory (for chpst)
    os.mkdir('.env')
    for key in ('GEM_HOME', 'SECRET_KEY_BASE', 'PASSWORD', 'GROUPNAME',
                'POSTGRES_HOST', 'POSTGRES_PORT', 'HOME', 'PATH',
                'BUNDLE_PATH'):
        # Bash
        with open('.profile', 'a', encoding='utf-8') as f:
            f.write('''\
export {key}="{value}"
'''.format(
                key=key, value=environ[key]))

        # Systemd
        with open('.envfile', 'a', encoding='utf-8') as f:
            f.write('''\
{key}="{value}"
'''.format(
                key=key, value=environ[key]))

        # Runit
        with open('.env/{}'.format(key), 'w', encoding='utf-8') as f:
            f.write(environ[key])

    with open('.profile', 'a', encoding="utf-8") as f:
        f.write('''
# Added by configure.py
export GEM_PATH="$GEM_HOME:/usr/lib/ruby/gems/2.4.0"
export GEM_CACHE="$GEM_HOME/cache"
'''.format(**environ))

    # create .gitconfig
    with open('.gitconfig', 'w', encoding="utf-8") as f:
        f.write('''
[credentials "https://github.com"]
    helper = store
[push]
    default = simple
[color]
    status = auto
    branch = auto
    interactive = auto
    diff = auto
[alias]
    lol = log --graph --decorate --pretty=oneline --abbrev-commit
    lola = log --graph --decorate --pretty=oneline --abbrev-commit --all
''')

    # Ruby gem config
    with open('.gemrc', 'w', encoding="utf-8") as f:
        f.write('gem: --user-install\n')
    subprocess.check_call(
        ['gem', 'install', 'bundler'],
        env=os.environ,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr)

    # Postgresql config
    with open('.pgpass', 'w', encoding="utf-8") as f:
        f.write('{POSTGRES_HOST}:{POSTGRES_PORT}:'
                '{GROUPNAME}:{GROUPNAME}:{PASSWORD}\n'.format(**environ))
    os.chmod(".pgpass", mode=0o0600)

    # Create .ssh/authorized_keys
    os.mkdir(".ssh")
    os.chmod(".ssh", mode=0o0700)
    with open('.ssh/authorized_keys', 'w') as f:
        f.write('\n'.join(user.ssh_keys))
    os.chmod(".ssh/authorized_keys", mode=0o0600)

    os.mkdir("config")
    with open('config/nginx.conf', 'w') as f:
        f.write('''
upstream puma-{GROUPNAME} {{
    server unix:/tmp/puma-{GROUPNAME}.sock fail_timeout=0;
}}

server {{
    listen 80;
    server_name {GROUPNAME}.{HOSTNAME};

    client_max_body_size 4G;

    root /home/{GROUPNAME}/www/app/public;
    index index.html index.htm;

    access_log /home/{GROUPNAME}/logs/access.log;
    error_log /home/{GROUPNAME}/logs/error.log;

    location / {{
        try_files $uri/index.html $uri @rack;
    }}

    location @rack {{
        proxy_pass http://puma-{GROUPNAME};
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
    }}

    # Nice Ruby on Rails error messages instead of Nginx'
    error_page 500 501 502 503 504 505 /500.html;
    keepalive_timeout 10;
}}
'''.format(**environ))

    with open('config/puma.rb', 'w') as f:
        f.write('''\
#!/usr/bin/env puma

environment ENV['RACK_ENV'] || "production"

threads 0, 16
workers 1

directory "/home/{GROUPNAME}/www/app"
bind "unix:///tmp/puma-{GROUPNAME}.sock"

plugin :tmp_restart

stdout_redirect "/home/{GROUPNAME}/logs/puma.out", "/home/{GROUPNAME}/logs/puma.err", true
'''.format(**environ))

    os.mkdir("logs")

    # www
    os.makedirs("www/app/public")
    with open('www/app/config.ru', 'w', encoding='utf-8') as f:
        f.write('''\
run Proc.new {{ |env|
    ['200',
     {{'Content-Type' => 'text/plain; charset=utf-8'}},
     ["Hello {GROUPNAME}!\\n\\n",
      env .merge(ENV)
          .select {{ |k,v| k !~ /^(PASSWORD|SECRET_KEY_BASE)$/ }}
          .collect {{ |k,v| "#{{k}}:\\t#{{v}}" }}
          .flatten
          .join("\\n")]]
}}
'''.format(**environ))
    with open('www/app/Gemfile', 'w', encoding='utf-8') as f:
        f.write('''\
# frozen_string_literal: true
source 'https://rubygems.org'

gem 'puma'
gem 'rack'
''')

    os.chdir('www/app')
    subprocess.check_call(
        ['bundler', 'install'],
        env=os.environ,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr)

    return 0


def main():
    environ = {}
    environ["GEM_HOME"] = ".gem/ruby/2.4.0"
    environ["POSTGRES_HOST"] = os.environ.get('POSTGRES_HOST', POSTGRES_HOST)
    environ["POSTGRES_PORT"] = "5432"

    with tempfile.NamedTemporaryFile() as fp:
        logging.info('create temporary .pgpass')
        fp.write(
            bytearray('{}:*:*:postgres:{}'.format(environ["POSTGRES_HOST"],
                                                  "root"), 'utf-8'))
        fp.seek(0)
        os.chmod(fp.name, mode=0o600)
        environ['PGPASSFILE'] = fp.name

        for user in USERS:
            password = pwgen()
            environ["GROUPNAME"] = user.name
            environ["PASSWORD"] = password
            environ["HOSTNAME"] = HOSTNAME
            environ["SECRET_KEY_BASE"] = "{:0128x}".format(
                random.randrange(16**128))

            create_user(user, password)
            p = multiprocessing.Process(target=init_user, args=(user, environ))
            p.start()
            p.join()

            logger.info('give rights to www-data to our folders')

            # Give rights to nginx
            homedir = "/home/{}".format(user.name)
            os.chdir(homedir)
            subprocess.check_call(
                [
                    "setfacl", "-R", "-m", "user:www-data:rwx", "config",
                    "www", "logs"
                ],
                stdout=sys.stdout,
                stderr=sys.stderr)
            subprocess.check_call(
                [
                    "setfacl", "-dR", "-m", "user:www-data:rwx", "config",
                    "www", "logs"
                ],
                stdout=sys.stdout,
                stderr=sys.stderr)
            # enable site in nginx
            os.symlink("{}/config/nginx.conf".format(homedir),
                       "/etc/nginx/sites-enabled/{}.conf".format(user.name))
            # Puma
            os.makedirs('/etc/service', exist_ok=True)  # if no runit
            os.mkdir('/etc/service/puma-{}'.format(user.name))
            with open('/etc/service/puma-{}/run'.format(user.name), 'w') as f:
                f.write('''\
#!/bin/sh

export HOME="/home/{user.name}"
export PATH="$PATH:$HOME/{gem_home}/bin"
cd "$HOME/www/app"

ENV_DIR="$HOME/.env"
PUMA_ENV="../../config/puma.rb"
COMMAND="bundle exec puma --config $PUMA_ENV"

exec 2>&1
exec chpst -u "{user.name}" -e "$ENV_DIR" $COMMAND
                    '''.format(
                    user=user, gem_home=environ["GEM_HOME"]))
            # Systemd
            os.makedirs(
                '/etc/systemd/system/multi-user.target.wants',
                exist_ok=True)  # if no systemd
            with open(
                    '/etc/systemd/system/multi-user.target.wants/puma-{}.service'.
                    format(user.name), 'w') as f:
                f.write('''\
[Unit]
Description=Puma HTTP Server for {user.name}
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/{user.name}/www/app
User={user.name}
EnvironmentFile=-/home/{user.name}/.envfile
ExecStart=bundle exec puma --config ../../config/puma.rb

[Install]
WantedBy=multi-user.target
''')

            os.chmod('/etc/service/puma-{}/run'.format(user.name), 0o0755)
            with open(
                    '/etc/sudoers.d/{}'.format(user.name), 'w',
                    encoding='utf-8') as f:
                f.write('''\
# runit
{user.name} ALL = (root) NOPASSWD: /usr/bin/sv restart nginx, /usr/bin/sv reload nginx
{user.name} ALL = (root) NOPASSWD: /usr/bin/sv restart puma-{user.name}, /usr/bin/sv reload puma-{user.name}
# systemd
{user.name} ALL = (root) NOPASSWD: /usr/bin/systemctl nginx restart, /usr/bin/systemctl nginx reload
{user.name} ALL = (root) NOPASSWD: /usr/bin/systemctl puma-{user.name} restart, /usr/bin/systemctl puma-{user.name} restart
                    '''.format(user=user))
            os.chmod('/etc/sudoers.d/{}'.format(user.name), 0o0600)

            logging.info('create postgresql database')
            p = subprocess.Popen(
                ['psql', '-h', environ['POSTGRES_HOST'], '-U', 'postgres'],
                env=environ,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)

            stdin = '''\
DROP DATABASE IF EXISTS {user.name};
DROP ROLE IF EXISTS {user.name};
CREATE ROLE {user.name} WITH NOINHERIT LOGIN PASSWORD '{password}' VALID UNTIL 'infinity';
CREATE DATABASE {user.name} WITH ENCODING 'UTF8' OWNER {user.name};
REVOKE ALL PRIVILEGES ON DATABASE {user.name} FROM public;
GRANT ALL PRIVILEGES ON DATABASE {user.name} TO {user.name};
\\c {user.name}
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA {user.name} AUTHORIZATION {user.name};
CREATE SCHEMA production AUTHORIZATION {user.name};
CREATE SCHEMA test AUTHORIZATION {user.name};
            '''.format(
                user=user, password=password)

            out, err = p.communicate(bytearray(stdin, 'utf-8'))
            if p.returncode != 0:
                logger.error(err.decode('utf-8'))
            else:
                logger.info(out.decode('utf-8'))


if __name__ == "__main__":
    main()
