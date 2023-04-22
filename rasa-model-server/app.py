from flask import Flask, render_template, send_from_directory, abort, request, jsonify
import os
from functools import wraps
from werkzeug.utils import secure_filename
from config import models_dir, server_port
from filesystem import Scaner

ALLOWED_EXTENSIONS = {'tar.gz'}
API_KEY = os.environ.get('API_KEY', None)
API_KEY_HEADER = "API-KEY"
DEBUG = os.environ.get('DEBUG', "0")

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_REQUEST_SIZE_MB', 64)) * 1000 * 1000


def require_apikey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        if request.headers.get(API_KEY_HEADER) and request.headers.get(API_KEY_HEADER) == API_KEY:
            return view_function(*args, **kwargs)
        else:
            abort(401, description="Invalid API Key, access denied")
    return decorated_function


@app.route('/', methods=['GET'])
@require_apikey
def index():
    return list_dir(models_dir)


@app.route('/<path:path>', methods=['GET'])
def serve(path):
    fetch_latest = '@latest' in path
    real_path = os.path.join(models_dir, path.replace('@latest', ''))
    if not os.path.exists(real_path):
        return 'Not Found', 404

    if os.path.isdir(real_path):
        if fetch_latest:
            latest_entry = Scaner(real_path).latest_entry
            if not latest_entry:
                return 'No Models Found', 404
            print('latest_entry', latest_entry.path, flush=True)
            return download_file(latest_entry.path)
        else:
            return list_dir(real_path)
    else:
        return download_file(real_path)


def list_dir(path):
    rel_path = os.path.relpath(path, models_dir)
    parent_path = os.path.dirname(rel_path)
    return render_template('index.html', sep=os.sep, parent_path=parent_path, path=rel_path, entries=Scaner(path).entries)


def download_file(path):
    return send_from_directory(os.path.dirname(path), os.path.basename(path), as_attachment=True)


@app.errorhandler(401)
def server_error(e):
    return jsonify(error=str(e)), 401


@app.route('/upload/<filename>', methods=['POST'])
@require_apikey
def upload_model(filename):
    if filename and allowed_file(filename):
        filename = secure_filename(filename)
        with open(os.path.join(models_dir, filename), "wb") as fp:
            fp.write(request.data)
        result = {'msg': 'File uploaded successfully'}
        return result, 201
    return {'msg': 'No file or file extension not allowed'}, 400


def allowed_file(filename):
    return '.' in filename and \
           filename.split('.', 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=server_port, debug=(DEBUG == "1"))

# flake8: noqa: E501
