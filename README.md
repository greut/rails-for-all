# Rails for all

Some scripts to create tons of Ruby on Rails setups on one "Ubuntu" machine.

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

- [ ] create systemd script for puma-*
