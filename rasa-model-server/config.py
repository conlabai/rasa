from os import environ

models_dir = environ.get('MODELS_DIR', 'models')
server_port = environ.get('PORT', 8080)