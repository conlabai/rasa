docker run -it --env-file .env \
-v  $(pwd)/endpoints.yml:/app/endpoints.yml \
-v $(pwd)/rasa-model/models:/app/models \
-v $(pwd)/rasa-server/credentials.yml:/app/credentials.yml \
-v $(pwd)/rasa-server/channels:/app/channels  \
--network dbt_default -p 0.0.0.0:8888:5005 eremeye/rasa-idl:dbt run --enable-api --debug
