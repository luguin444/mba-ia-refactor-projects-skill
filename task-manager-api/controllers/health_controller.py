from datetime import datetime

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


def index():
    return {'message': API_NAME, 'version': API_VERSION}


def health():
    # Hora local do servidor, como no original (os campos *_at das entidades é que são UTC).
    return {'status': 'ok', 'timestamp': str(datetime.now())}
