#!/usr/bin/env python3
"""
Create tons of users and set up their Ruby on Rails installation.

/home/user/conf/nginx.conf
               /puma.rb
          /www/...
          /.ssh/authorized_keys
          /.profile
"""

import multiprocessing
import os
import pwd
import random
import subprocess
import sys

from collections import namedtuple

User = namedtuple('User', 'name ssh_keys')

id_rsa_pub = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDVHwpNj+Fdh2zfi+SXnJrOFqC0Z30VV8ta5aaXUCPvas9sDDDZyEXRdwdbydUkLyXd9a/6eHD5I//JmZ0FKT4zRqtB5Xwu+gjMGVtMXc+qsAPIMPsrYGRYHL14m6prQB4myjTJZmGB5Auf9N6rYFOE01bkoZfU3wYpwZP0t2vCAYJwoN20d5H87i0KB6SngamdgIMXH+h7lJcbBGZBxGTL4r0U1SqLTkTGCZ/+7JYQJWNAZKZtMvCyx7KKI03ZR0+SjFSMIurtS8tiVHyAgZ2luyKtH6NlR6O7RDZr0aeONnbDIDHnoaOxVSlTDxHcTXfFDhZhkCTiHUUyr2eseIpH yoan@x1'

users = User('yoan', [id_rsa_pub, ]), User('david', [id_rsa_pub, ])


def pwgen(length=64):
    """Generate a secure password."""
    proc = subprocess.Popen(
        ["pwgen", "--secure", "{}".format(length), "1"],
        stdout=subprocess.PIPE)
    return proc.communicate()[0].decode().strip()


def create_user(user, password, groupname):
    subprocess.check_call(
        [
            "useradd", user.name, "--create-home", "--shell", "/bin/bash",
            "--groups", groupname
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)

    proc = subprocess.Popen(
        ["chpasswd", ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    proc.communicate("{}:{}".format(user.name, password).encode("utf-8"))


def init_user(user, environ):
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

    # update .profile with environ
    with open('.profile', 'a', encoding="utf-8") as f:
        f.write('''
# Added by configure.py
GEM_HOME="$HOME/{GEM_HOME}"
GEM_PATH="$GEM_HOME:/usr/lib/ruby/gems/2.4.0"
GEM_CACHE="$GEM_HOME/cache"
PATH="$PATH:$GEM_HOME/bin"
SECRET_KEY_BASE="{SECRET_KEY_BASE}"
GROUPNAME="{GROUPNAME}"
PASSWORD="{PASSWORD}"
POSTGRES_HOST="{POSTGRES_HOST}"
POSTGRES_PORT="{POSTGRES_PORT}"
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

    os.mkdir("conf")
    with open('conf/nginx.conf', 'w') as f:
        f.write('''
upstream puma-{GROUPNAME} {{
    server unix:/tmp/{GROUPNAME}/puma.sock fail_timeout=0;
}}

server {{
    listen 80;
    server_name {GROUPNAME}.{HOSTNAME};

    client_max_body_size 4G;

    root /home/{GROUPNAME}/www;
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
    os.mkdir("www")
    os.mkdir("logs")

    return 0


def main():
    groupname = "developers"  # for sv
    hostname = "capistrano"
    environ = {}
    environ["GEM_HOME"] = ".gem/ruby/2.4.0"
    environ["POSTGRES_HOST"] = os.environ.get('POSTGRES_HOST', "localhost")
    environ["POSTGRES_PORT"] = "5432"

    for user in users:
        password = pwgen()
        environ["GROUPNAME"] = user.name
        environ["PASSWORD"] = password
        environ["HOSTNAME"] = hostname
        environ["SECRET_KEY_BASE"] = "{:0128x}".format(
            random.randrange(16**128))

        create_user(user, password, groupname)
        p = multiprocessing.Process(target=init_user, args=(user, environ))
        p.start()
        p.join()

        # Give rights to nginx
        homedir = "/home/{}".format(user.name)
        os.chdir(homedir)
        subprocess.check_call(
            [
                "setfacl", "-R", "-m", "user:www-data:rwx", "conf", "www",
                "logs"
            ],
            stdout=sys.stdout,
            stderr=sys.stderr)
        subprocess.check_call(
            [
                "setfacl", "-dR", "-m", "user:www-data:rwx", "conf", "www",
                "logs"
            ],
            stdout=sys.stdout,
            stderr=sys.stderr)
        # Symlink
        os.symlink("{}/conf/nginx.conf".format(homedir),
                   "/etc/nginx/sites-enabled/{}.conf".format(user.name))
        # TODO: /etc/service/puma-groupname/run


if __name__ == "__main__":
    main()
