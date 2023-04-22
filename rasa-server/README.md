# rasa-service: rasa server for Iditelesom

## Local installation

1. Install Python 3.7 on your local machine
1. Clone this repository, creates a directory `rasa-idl`
1. `cd rasa-idl/rasa-service`
1. Create and activate a virtual environment:

    ```bash
    python -venv venv
    source venv/bin/activate
    ```

1. Install rasa with the `spacy` plugin

    ```bash
    pip install 'rasa[spacy]'
    ```

1. Install the spacy large Russian language model

    ```bash
    python -m spacy download ru_core_news_lg
    ```

1. Congrats! Rasa is installed. You now can work with the `rasa` commands:

    ```bash
    rasa train nlu # train model
    rasa shell nlu # converse with model
    rasa test nlu # test the model
    ```

## Rasa files

* config.yaml - language and training pipeline
* domain.yaml - intents and session settings
* data/nlu.yaml - examples for intents

## Training the model

Training will use cached training results if the training data did not change.

## Testing the model

For testing, use the command `rasa test nlu`. This will look in the directory `tests` and run tests according to stories specified there. Results will be written to the directory `results`.

## Rasa X installation and use

Install rasa:

```bash
  cd rasa-idl
  source venv/bin/activate
  pip install rasa-x
```

Start rasa:

```bash
  rasa x
```

You will see a lot of messages, with at the end something like this in green letters: 

`The server is running at http://localhost:5002/login?username=admin&password=y9lPCtuB9j9S`

You can login to your local Rasa X with the supplied credentials.

*Note*: for Rasa X to support reading and writing model files, they should contain the following keypair:

```yaml
version: "3.0"
```

at the top of the file.
