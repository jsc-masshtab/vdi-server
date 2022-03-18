FROM python:3.7-slim-buster
WORKDIR /opt/veil-vdi/app
COPY devops/deb/veil-broker-backend/root/usr/sbin/* /usr/sbin/
COPY devops/docker/python/tests_entry_point.sh /usr/sbin/tests_entry_point.sh
COPY devops/docker/python/systemctl /usr/sbin/systemctl
COPY devops/docker/python/vdi_update_web_statistics.sh /usr/sbin/vdi_update_web_statistics.sh
ADD backend/*requirements.txt ./
RUN chmod 777 /usr/sbin/systemctl /usr/sbin/vdi_update_web_statistics.sh && \
    apt-get update && apt-get install -y iproute2 python3-dev \
    python3-setuptools python-dev gcc python3-pip libsasl2-dev \
    libldap2-dev libssl-dev sudo && \
    pip install -r requirements.txt && pip install -r dev-requirements.txt
