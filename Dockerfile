FROM ubuntu:yakkety
LABEL maintainer="Yoan Blanc <yoan@dosimple.ch>"

ENTRYPOINT ["/tini", "--"]

# Install all the stuff aside
ADD install.sh /
RUN sh /install.sh \
 && rm /install.sh

EXPOSE 22 80

# Runit
ADD nginx.sh /etc/service/nginx/run
ADD sshd.sh /etc/service/sshd/run
RUN chmod +x /etc/service/nginx/run \
 && chmod +x /etc/service/sshd/run

# Bootstrap
ADD boot.sh /usr/local/bin/boot.sh
ADD configure.py /usr/local/bin/configure.py
RUN chmod +x /usr/local/bin/boot.sh \
 && chmod +x /usr/local/bin/configure.py

CMD [ "/usr/local/bin/boot.sh" ]
