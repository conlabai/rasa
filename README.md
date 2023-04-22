# rasa-chatwoot: Conlab rasa stack for Chatwoot integration

## Contents of the repo

This repo contains all components needed to run a Iditelesom Rasa stack. Every component lives inside its own subdirectory:

1. rasa-server: the Rasa server with the Chatwoot channel
1. rasa-model-server: the Rasa model server - serving models to Rasa service
1. rasa-nlg-server: the Rasa NLG server - called by Rasa output engine and does optional lookup in Chatwoot
1. rasa-action-server: the Rasa action server - called by Rasa when a custom action needs to be run
1. rasa-model: this contains the training files for the model

## Running a development environment

```
./rundev.sh
````

This will start all services using docker compose.

## Training the model

```bash
./train.sh
```

The resulting model will be will be written to the directory rasa-model/models.

## running rasa commands

```bash
./rasa.sh
```
This will start the rasa container so you can issue rasa commands such as `rasa cli`.