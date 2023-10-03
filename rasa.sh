#/bin/bash
# start rasa in a container with training data and model mounted
#--gpus=all \
#-v rasa-idl_rasa-models:/app/models \
# docker run -it -u root \
docker run -it \
--user $(id -u):$(id -g) \
--gpus=all \
--env-file .env \
-v $(pwd)/rasa-model:/app \
-v $(pwd)/endpoints.yml:/app/endpoints.yml \
-v $(pwd)/rasa-server/credentials.yml:/app/credentials.yml \
-v $(pwd)/rasa-server/channels:/app/channels \
--network rasa-chatwoot_default \
--entrypoint bash \
-p 5005:5005 \
conlab/rasa:chatwoot-gpu
