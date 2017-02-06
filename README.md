# Rails for all

Some scripts to create tons of Ruby on Rails setups on one "Ubuntu" machine.

## Configure

We need to have either a structure in `configure.py` or a json file.

```console
$ python github_keys.py GITHUB_USER GITHUB_KEY < students.tsv > accounts.json
```

If you prefer the hardcoded settings, create an empty `accounts.json` file.

## How to...

```console
$ docker-compose build
$ # go take a coffee.

$ docker-compose up -d
$ # check your twitter feed

$ ssh yoan@localhost
$ open http://yoan.capistrano:8080/
```

## Variables

In `configure.py`

- `USERS` the users to be created, add your's and the SSH public key.
- `HOSTNAME` it currently says `capistrano`.

For local development, put the hostname into your `/etc/hosts`.

## TODO

Currently, it's configured against runit, but should be adapted for the real systemd deal.

- [x] create systemd script for puma-username
- [ ] test systemd script for puma-username
