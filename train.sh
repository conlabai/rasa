#/bin/bash

cd rasa-model
docker run -it -u root \
-v $(pwd):/app \
-v $(pwd)/models:/app/models \
--gpus=all \
eremeye/rasa:chatwoot-gpu train
# --mount type=bind,source="$(pwd)"/endpoints.yml,target=/app/endpoints.yml,readonly \
