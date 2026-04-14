ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION}
ARG NETBOX_VERSION
ENV PYTHONUNBUFFERED 1
RUN set -x \
    && cd /opt \
    && adduser --system --group netbox \
    && curl -sSLO https://github.com/netbox-community/netbox/archive/refs/tags/v${NETBOX_VERSION}.tar.gz \
    && tar xzf v${NETBOX_VERSION}.tar.gz \
    && mv -fv /opt/netbox-${NETBOX_VERSION} /opt/netbox 
    # && chown -cR netbox:root /opt/netbox/netbox/media

RUN set -x \
    && cd /opt \
    && pip install --no-cache-dir --upgrade pip wheel \
    && pip install debugpy \    
    && pip install netboxlabs-netbox-custom-objects==0.4.3 \
    && pip install --no-cache-dir poetry -r netbox/requirements.txt

WORKDIR /opt/netbox_device_view

COPY .. /opt/netbox_device_view

RUN pip install --no-cache-dir .

WORKDIR /opt/netbox/netbox

COPY develop/configuration.py /opt/netbox/netbox/netbox/

RUN set -x && python manage.py collectstatic --no-input
