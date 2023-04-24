# rasa-server: rasa server for Chatwoot

## Contents

* channels - this folder contains a custom Chatwoot channel. For its configuration, see `credentials.yml`.
* credentials.yml - example configuration for the Chatwoot rasa channel.
* Dockerfile - build a default rasa image 
* Dockerfile.spacy - build a rasa image with the large Spacy language model (russian)
* Dockerfile.gpu - build a rasa image with Spacy and configured to work on a gpu
* requirements.txt - python requirements used by image builds

## Local image build

(in parent directory)
docker compose build rasa-small
docker compose build rasa
docker compose build rasa-gpu


