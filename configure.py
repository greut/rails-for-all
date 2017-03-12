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

import json
import multiprocessing
import os
import logging
import pwd
import random
import subprocess
import sys
import tempfile
import time

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

with open('/root/accounts.json', 'r', encoding='utf-8') as f:
    USERS = json.load(f)

if not len(USERS):
    logger.info('accounts.json is empty. Using the hardcoded folks.')
    USERS = {
        'yoanb': {
            'firstname': 'Yoan',
            'lastname': 'Blanc',
            'keys':
            ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDVHwpNj+Fdh2zfi+SXnJrOFqC0Z30VV8ta5aaXUCPvas9sDDDZyEXRdwdbydUkLyXd9a/6eHD5I//JmZ0FKT4zRqtB5Xwu+gjMGVtMXc+qsAPIMPsrYGRYHL14m6prQB4myjTJZmGB5Auf9N6rYFOE01bkoZfU3wYpwZP0t2vCAYJwoN20d5H87i0KB6SngamdgIMXH+h7lJcbBGZBxGTL4r0U1SqLTkTGCZ/+7JYQJWNAZKZtMvCyx7KKI03ZR0+SjFSMIurtS8tiVHyAgZ2luyKtH6NlR6O7RDZr0aeONnbDIDHnoaOxVSlTDxHcTXfFDhZhkCTiHUUyr2eseIpH',
             )
        },
        #        'david': {
        #            'firstname': 'David',
        #            'lastname': 'Grunenwald',
        #            'keys':
        #            ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCYNRTPsKPGniLSzrzhar2N5b90+At1ejBzoRQP3orxcBdRkcNlFdGVL1fk4nYx1GXZNUT9P0Z+jiQjXAk2B/otIEzsBZ+JrkviplWAYZ7qYAZUlTh9o6PdechQlxtAZO4Tys6k0K15GLtZboK7KHJOme5tEszRGGDcFsQRR7QUUM7g39dckUlrfNxkeU196Vo+ZKJ2sDGCc0Pbrm4hCTL/1UzDTVZs7nV0kpnpOXNXKdjGtkwEc03+kcRPs9eb1KKiKxFdHxjc+F56kklF54s/cY8TTyw79SFDRD3/Hc36ldhxGrgxoSKFhVIWyF3mA+n5E87L8H0fsh3MLb1BlIgCMIE82Va9o60a5a9a/Aba+odaMmB/NBO3uD6TX7Ny1Cq61vXa8jnW07/aSYFdPy4r/Y4xW7eovuldRHpdGZub7hwkoUpKc7Iechgcqf+u2JFsfovpGNPBTclVqrBpUJ66y54Gj5SHhgOPRJoMgMN/PNTdAGyZVGDWbGWT5OuVWFF4Q4y/hOJGQSbGaq68Kft6IzLRF0owQctKahwJ1JZEVv3iSLI+NodfdZPxgBqSkZDCZNs6BK2HoPqIjmR5ECkT2ePWAT54cwwlu6DoyymytOTVyCBTQreuDo/zd9Id9fPfAWwrhCs8qYZ7Vgd3Cg97v+M55Vah2vI9HEmVN/Lpzw==',
        #             'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpcwue83WhRX49KkdKP3YfkigBiFaLaQjwmEfHy2RbS2ub9GOPCxX9k0vK2lUm0hTg8iFRJIKla/dsJ1H2fH2hMfqnJ0d5MRIA6uaHVu4huNtNkFAGNy5C2SgYhENqp49iUSs0D3DoEq72n2e9cqGlxWbq3KBHcb6GJY/Z5Z8vRvdzM8PUMAlTQj2N2Q0vi+RtryHIj7zr2fwlwAlex0A+NtshT9+80EHJZS2aizOIHeF3zKkFSJ1+6ttEBj0hTN6Alzk9+h0F0obgt1LYGkYohhkcQuQ0k0tb6fVgsymlo1vopIBzUGXCXtygCpVaFe6W3MZnoIv4lCceNTzRn+m5'
        #             )
        #        },
        #        'raphael': {
        #            'firstname': 'Raphaël',
        #            'lastname': 'Emourgeon',
        #            'keys':
        #            ('ssh-dss AAAAB3NzaC1kc3MAAACBAOzL/oLzDj3wRYhMl+EAv7vExo/Ss4Qk5RAXBfwnJVu1Nm8d1h/TY4uaxDlbBoKDitqe4i5Qqt8NTpl576qCPyrnZqfjDQAKsVtSt+Vv0Gf5OqUE+MFr89EWa/Y5fh0cOe7etPZ8PjrRJiicZHcKMLcXakLedGaL2MMsN9zTKnDDAAAAFQCh+kmfSr+CDHe9Q07Bm1iS1bizRwAAAIBK04rSeNxOmTOOBzWDQz0Kk5I6dTrApXwc+4Alj9XjjKHcV1HFwmFbOm2eQFU0pTOcNo7WhW4zvI6O9shLBgW2CVmrfNOXrR/GORlK/ZbMFFpoQMsuOo/PDb8piV8G3bgHO1+N3gLlfMq+GG+ceBo0jBhjQh9XLe3HvWKkvEy9vQAAAIEA4O05TWpIZTiaihPYiZ1ieTklaF6cWftgp/rXumaat8q4nC6lhi4h5LSP/x7N0zNLj7WVFkzhoa+ESwQKBIRQkLj6/2XPATTEs2Lg2wMbFasvDvUo0PJMZADd2p4OuVXQ913qXzQgPQwJ5Q+n2PQkLRWH+eNmxh8O8b2ToTbTKi8=',
        #             )
        #        }
    }

HOSTNAME = os.environ.get("HOSTNAME", "capistrano")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "root")

SYSTEMD = "RUNIT" not in os.environ
RUNIT = "RUNIT" in os.environ


def pwgen(length=64):
    """Generate a secure password."""
    proc = subprocess.Popen(
        ["pwgen", "--secure", "{}".format(length), "1"],
        stdout=subprocess.PIPE)
    return proc.communicate()[0].decode().strip()


def create_user(user, password, comment=""):
    logger.info('create user %s', user)
    subprocess.check_call(
        [
            "useradd", user, "--create-home", "--shell", "/bin/bash",
            "--comment", comment.encode('ascii', 'ignore')
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)

    proc = subprocess.Popen(
        ["chpasswd", ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    proc.communicate("{}:{}".format(user, password).encode("utf-8"))


def init_user(user, keys, environ):
    logger.info('init user %s', user)
    p = pwd.getpwnam(user)
    uid, gid = p.pw_uid, p.pw_gid
    homedir = p.pw_dir

    # os
    os.initgroups(user, gid)
    os.setgid(gid)
    os.setuid(uid)
    os.umask(0o027)
    os.chdir(homedir)

    # env
    os.environ["USER"] = user
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

        if SYSTEMD:
            with open('.envfile', 'a', encoding='utf-8') as f:
                f.write('''\
    {key}="{value}"
    '''.format(
                    key=key, value=environ[key]))

        if RUNIT:
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
        f.write('\n'.join(keys))
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


def init_postgres(password):
    p = pwd.getpwnam('postgres')
    uid, gid = p.pw_uid, p.pw_gid
    homedir = p.pw_dir

    os.initgroups('postgres', gid)
    os.setgid(gid)
    os.setuid(uid)
    os.chdir(homedir)

    subprocess.check_call([
        'psql', '-c',
        "ALTER USER postgres WITH PASSWORD '{}';".format(password)
    ])


def main(argv):
    environ = {}
    environ["GEM_HOME"] = ".gem/ruby/2.4.0"
    environ["POSTGRES_HOST"] = POSTGRES_HOST
    environ["POSTGRES_PORT"] = "5432"

    delete = False if len(argv) < 2 else argv[1] == 'DELETE'

    # Handle a local Postgres setup.
    if POSTGRES_HOST == 'localhost':
        logger.info('init postgres (with 5s of pause)')

        # Wait for Postgres
        time.sleep(5)
        p = multiprocessing.Process(
            target=init_postgres, args=(POSTGRES_PASSWORD, ))
        p.start()
        p.join()

    with tempfile.NamedTemporaryFile() as fp:
        logging.info('create temporary .pgpass')
        fp.write(
            bytearray('{}:*:*:postgres:{}'.format(environ["POSTGRES_HOST"],
                                                  POSTGRES_PASSWORD), 'utf-8'))
        fp.seek(0)
        os.chmod(fp.name, mode=0o600)
        environ['PGPASSFILE'] = fp.name

        for user, config in USERS.items():
            if delete:
                sure = input('Are you sure, you wand to delete {}: '.format(
                    user))
                if sure[0] not in 'yYoO1':
                    continue
                if SYSTEMD:
                    subprocess.call(
                        ['systemctl', 'disable', 'puma-{}'.format(user)])
                    subprocess.check_call([
                        'rm', '-f',
                        '/etc/systemd/system/puma-{}.service'.format(user)
                    ])
                    subprocess.check_call(['systemctl', 'daemon-reload'])
                subprocess.call([
                    'rm', '-f', '/etc/nginx/sites-enabled/{}.conf'.format(user)
                ])
                subprocess.call(['gpasswd', '-d', 'www-data', user])
                subprocess.call(['userdel', user])
                subprocess.call(['groupdel', user])
                subprocess.check_call(['rm', '-rf', '/home/{}'.format(user)])
                continue

            password = pwgen()
            environ["GROUPNAME"] = user
            environ["PASSWORD"] = password
            environ["HOSTNAME"] = HOSTNAME
            environ["SECRET_KEY_BASE"] = "{:0128x}".format(
                random.randrange(16**128))

            create_user(
                user,
                password,
                comment="{firstname} {lastname}".format(**config))
            p = multiprocessing.Process(
                target=init_user, args=(user, config['keys'], environ))
            p.start()
            p.join()

            # Add hostname
            with open('/etc/hosts', 'a', encoding='utf-8') as f:
                f.write('''127.0.0.1 {GROUPNAME}.{HOSTNAME}\n'''.format(
                    **environ))

            # Give rights to nginx
            logger.info('give rights to www-data to our folders')
            subprocess.check_call(
                ['usermod', '-aG', user, 'www-data'],
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)

            subprocess.check_call(
                [
                    'setfacl', '-dR', '-m', 'user:{}:rw-'.format(user),
                    '/home/{}/logs'.format(user)
                ],
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)

            # enable site in nginx
            os.symlink("/home/{}/config/nginx.conf".format(user),
                       "/etc/nginx/sites-enabled/{}.conf".format(user))
            # Puma
            if RUNIT:
                os.makedirs('/etc/service', exist_ok=True)  # if no runit
                os.mkdir('/etc/service/puma-{}'.format(user))
                with open('/etc/service/puma-{}/run'.format(user), 'w') as f:
                    f.write('''\
#!/bin/sh

export HOME="/home/{user}"
export PATH="$PATH:$HOME/{gem_home}/bin"
cd "$HOME/www/app"

ENV_DIR="$HOME/.env"
PUMA_ENV="../../config/puma.rb"
COMMAND="bundle exec puma --config $PUMA_ENV"

exec 2>&1
exec chpst -u "{user}" -e "$ENV_DIR" $COMMAND
                    '''.format(
                        user=user, gem_home=environ["GEM_HOME"]))
                os.chmod('/etc/service/puma-{}/run'.format(user), 0o0755)

            if SYSTEMD:
                os.makedirs('/etc/systemd/system', exist_ok=True)
                with open('/etc/systemd/system/puma-{}.service'.format(user),
                          'w') as f:
                    f.write('''\
[Unit]
Description=Puma HTTP Server for {user}
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/{user}
User={user}
EnvironmentFile=-/home/{user}/.envfile
ExecStart=/home/{user}/{gem_home}/bin/puma --config config/puma.rb

[Install]
WantedBy=multi-user.target
'''.format(
                        user=user, gem_home=environ["GEM_HOME"]))

                subprocess.check_call(
                    ['systemctl', 'enable', 'puma-{}'.format(user)],
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE)
                subprocess.check_call(
                    ['systemctl', 'start', 'puma-{}'.format(user)],
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE)

            with open(
                    '/etc/sudoers.d/{}'.format(user), 'w',
                    encoding='utf-8') as f:
                f.write('''\
# runit
{user} ALL = (root) NOPASSWD: /usr/bin/sv restart nginx, /usr/bin/sv reload nginx
{user} ALL = (root) NOPASSWD: /usr/bin/sv restart puma-{user}, /usr/bin/sv reload puma-{user}
# systemd
{user} ALL = (root) NOPASSWD: /bin/systemctl restart nginx, /bin/systemctl reload nginx
{user} ALL = (root) NOPASSWD: /bin/systemctl restart puma-{user}, /bin/systemctl reload puma-{user}
{user} ALL = (root) NOPASSWD: /usr/sbin/service nginx restart, /usr/sbin/service nginx reload
{user} ALL = (root) NOPASSWD: /usr/sbin/service puma-{user} restart, /usr/sbin/service puma-{user} reload
'''.format(user=user))
            os.chmod('/etc/sudoers.d/{}'.format(user), 0o0600)

            logging.info('create postgresql database')
            p = subprocess.Popen(
                ['psql', '-h', environ['POSTGRES_HOST'], '-U', 'postgres'],
                env=environ,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)

            stdin = '''\
DROP DATABASE IF EXISTS {user};
DROP ROLE IF EXISTS {user};
CREATE ROLE {user} WITH NOINHERIT LOGIN PASSWORD '{password}' VALID UNTIL 'infinity';
CREATE DATABASE {user} WITH ENCODING 'UTF8' OWNER {user};
REVOKE ALL PRIVILEGES ON DATABASE {user} FROM public;
GRANT ALL PRIVILEGES ON DATABASE {user} TO {user};
\\c {user}
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA {user} AUTHORIZATION {user};
CREATE SCHEMA production AUTHORIZATION {user};
CREATE SCHEMA test AUTHORIZATION {user};
            '''.format(
                user=user, password=password)

            out, err = p.communicate(bytearray(stdin, 'utf-8'))
            if p.returncode != 0:
                logger.error(err.decode('utf-8'))
            else:
                logger.info(out.decode('utf-8'))


if __name__ == "__main__":
    main(sys.argv)
