<p align="center">
    <img src="https://user-images.githubusercontent.com/5860071/61949755-7dbca580-afb4-11e9-87b6-1187933cccfb.png" width="200" border="0" alt="rasa-model-server">
    <br/>
    <a href="https://github.com/vrachieru/rasa-model-server/releases/latest">
        <img src="https://img.shields.io/badge/version-1.0.0-brightgreen.svg?style=flat-square" alt="Version">
    </a>
    <a href="https://hub.docker.com/r/vrachieru/rasa-model-server/">
        <img src="https://img.shields.io/docker/stars/vrachieru/rasa-model-server.svg?style=flat-square" />
    </a>
    <a href="https://hub.docker.com/r/vrachieru/rasa-model-server/">
        <img src="https://img.shields.io/docker/pulls/vrachieru/rasa-model-server.svg?style=flat-square" />
    </a>
    <br/>
    Simple webserver for externalizing RASA models.
</p>

### About

You can [configure RASA to fetch models](https://rasa.com/docs/rasa/user-guide/running-the-server/#fetching-models-from-a-server) from this server either by:  
1. pointing to a specific model (`.tar.gz`) and overriding said file when you want the model to change  
`http://localhost:8080/bot/model.tar.gz`  
2. pointing to a folder (suffixing the url with `@latest`) containing multiple models (`.tar.gz`) and getting the latest model sorted by modified date  
`http://localhost:8080/bot@latest`

### Quick start

I recommend pulling the [latest image](https://hub.docker.com/r/vrachieru/rasa-model-server/) from Docker hub as this is the easiest way:
```bash
$ docker pull vrachieru/rasa-model-server
```

If you'd like, you can build the Docker image yourself:
```bash
docker build -t <yourname>/rasa-model-server .
```

Specify your desired configuration and run the container:
```bash
$ docker run -<d|i> --rm \
    -v /host/path/to/models:/app/models \
    -p <host_port>:8080 \
    vrachieru/rasa-model-server
```

You can stop the container using: 
```bash
$ docker stop rasa-model-server
```


### Configuration

You can configure the service via the following environment variables.

| Environment Variable  | Default Value | Description                                             |
| --------------------- | ------------- | ------------------------------------------------------- |
| PORT                  | 8080          | Port on which to run the webserver.                     |
| MODELS_DIR            | models        | The absolute or relative location of the models folder. |


### Example

Fetch a model without specifying a `If-None-Match` header.
```
$ curl -s -I 'http://localhost:8080/bot/model.tar.gz'
HTTP/1.0 200 OK
Content-Disposition: attachment; filename=model.tar.gz
Content-Length: 6478848
Content-Type: application/x-tar
Last-Modified: Tue, 23 Apr 2019 12:28:43 GMT
Cache-Control: public, max-age=43200
Expires: Fri, 26 Jul 2019 23:42:05 GMT
ETag: "1556022523.364716-6478848-1948524791"
Date: Fri, 26 Jul 2019 11:42:05 GMT
Accept-Ranges: bytes
Server: Werkzeug/0.14.1 Python/3.6.3
```

Once the model is loaded by RASA, subsequent requests will use the received ETAG to check if the model has been updated.
```
$ curl -s -I 'http://localhost:8080/bot/model.tar.gz' -H 'If-None-Match: 1556022523.364716-6478848-1948524791'
HTTP/1.0 304 NOT MODIFIED
Content-Disposition: attachment; filename=model.tar.gz
Cache-Control: public, max-age=43200
Expires: Fri, 26 Jul 2019 23:42:48 GMT
ETag: "1556022523.364716-6478848-1948524791"
Date: Fri, 26 Jul 2019 11:42:48 GMT
Accept-Ranges: bytes
Server: Werkzeug/0.14.1 Python/3.6.3
```

Update the model on the server an the next request will pull the new model upon ETag mismatch.
```
$ curl -s -I 'http://localhost:8080/bot/model.tar.gz' -H 'If-None-Match: 1556022523.364716-6478848-1948524791'
HTTP/1.0 200 OK
Content-Disposition: attachment; filename=model.tar.gz
Content-Length: 900
Content-Type: application/x-tar
Last-Modified: Sat, 29 Dec 2018 23:17:54 GMT
Cache-Control: public, max-age=43200
Expires: Fri, 26 Jul 2019 23:43:32 GMT
ETag: "1546125474.453404-900-1948524791"
Date: Fri, 26 Jul 2019 11:43:32 GMT
Accept-Ranges: bytes
Server: Werkzeug/0.14.1 Python/3.6.3
```

### License

MIT