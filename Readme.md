# Web Front End for testssl.sh

[![GitHub Workflow - CI](https://github.com/jamespo/testssl.sh-webui/workflows/build/badge.svg)](https://github.com/jamespo/testssl.sh-webui/actions?workflow=build)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/jamespo/testssl.sh-webui)](https://github.com/jamespo/testssl.sh-webui/releases/latest)
[![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/jamespo7/testsslwebui?sort=semver)](https://hub.docker.com/repository/docker/jamespo7/testsslwebui)

This project is a web interface for [testssl.sh](https://testssl.sh/). It can be used to offer internal TLS/SSL configuration check portals, whereever the usual public tools are not applicable. It is available as Docker image.

Based on [mailsvb fork](https://github.com/mailsvb/testssl.sh-web).

## Installation

### Docker

`docker run -p 5000:5000 jamespo7/testsslwebui:latest`

In case you need to validate against specific root certificates, you can mount a folder containing your root certificates (*.pem) into the container. E.g.

`docker run -p 5000:5000 -v /your/certificates/folder/:/etc/ssl/certs/ jamespo7/testsslwebui:latest`

### Native

`git clone --recursive git@github.com:jamespo/testssl.sh-webui.git`

## Customization

A few optional environment variables are available, example usage:

	TESTSSL_CMD=/bin/testssl.sh
	TESTSSL_CA=/opt/homebrew/etc/openssl@3/cert.pem
	TESTSSL_WEB_HOST=127.0.0.1
	TESTSSL_WEB_PORT=5500

	CHECKTIMEOUT=120
	TESTSSLDEBUG=1

## NGINX Reverse Proxy

If you would like to run behind a NGINX Reverse Proxy simply add this to your configuration file in sites-enabled. 
If you want to add security to it look at nginx module [basic_auth](http://nginx.org/en/docs/http/ngx_http_auth_basic_module.html).

     location /testssl/ {
          proxy_pass http://127.0.0.1:5000/;
          gzip_types text/plain application/javascript;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_connect_timeout 200;  # you might need to increase these values depending on your server hardware. 
          proxy_send_timeout 200;     # you might need to increase these values depending on your server hardware. 
          proxy_read_timeout 200;     # you might need to increase these values depending on your server hardware. 
          send_timeout 200;           # you might need to increase these values depending on your server hardware. 
     }
