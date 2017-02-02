FROM ubuntu:yakkety
LABEL maintainer="Yoan Blanc <yoan@dosimple.ch>"

ENTRYPOINT ["/tini", "--"]

# Install all the stuff aside
ADD install.sh /
RUN sh /install.sh \
 && rm /install.sh

# Runit
ARG group=developers
ADD nginx.sh /etc/service/nginx/run
ADD sshd.sh /etc/service/sshd/run
RUN addgroup $group \
 && chmod +x /etc/service/nginx/run \
 && chmod +x /etc/service/sshd/run \
 && chgrp -R $group /etc/service/nginx

# Bootstrap
ADD boot.sh /usr/local/bin/boot.sh
ADD configure.py /usr/local/bin/configure.py
RUN chmod +x /usr/local/bin/boot.sh \
 && chmod +x /usr/local/bin/configure.py


EXPOSE 22 80

CMD [ "/usr/local/bin/boot.sh" ]
