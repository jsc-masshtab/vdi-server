FROM debian:buster-slim

# add pip proxy config
COPY pip.conf /root/.pip/

# install build-deps
RUN apt-get update && \
    apt-get install iproute2 python3-dev python3-setuptools python-dev gcc python3-pip \
    libsasl2-dev libldap2-dev libssl-dev sudo curl apt-utils rsync genisoimage wget gettext -y -q && \
    rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true

# install nodejs
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true

# install pip-deps
RUN /usr/bin/python3 -m pip install 'pip==21.3.1' 'tornado==6.1' 'virtualenv==16.7.12' \
        'Jinja2==3.0.0' 'mkdocs==1.2.3' 'mkdocs-material==7.3.6' 'pymdown-extensions==9.1' \
        'mkdocs-print-site-plugin==2.1' --force-reinstall \
        -i http://nexus.bazalt.team/repository/pypi-proxy/simple \
        --trusted-host nexus.bazalt.team