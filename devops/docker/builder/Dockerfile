FROM debian:stretch-slim

# add pip proxy config
COPY pip.conf /root/.pip/

# install build-deps
RUN apt-get update && \
    apt-get install python3-dev python3-setuptools python-dev gcc python3-pip \
    libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils rsync genisoimage wget gettext -y -q && \
    rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true

# install nodejs
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - && \
    apt-get install -y nodejs && \
    rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true

# install pip-deps
RUN /usr/bin/python3 -m pip --no-cache-dir install 'pip==20.3.4' --force-reinstall && \
    /usr/bin/python3 -m pip --no-cache-dir install 'tornado==5.1.1' 'virtualenv==15.1.0' 'mkdocs==1.1.2' \
    'mkdocs-material==7.1.2' 'pymdown-extensions==8.0' 'mkdocs-print-site-plugin==1.0.0' --force-reinstall