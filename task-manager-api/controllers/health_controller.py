"""Controller de diagnóstico e raiz da API."""
from flask import jsonify

from utils.helpers import utc_now

API_NAME = 'Task Manager API'
API_VERSION = '1.0'


def index():
    return jsonify({'message': API_NAME, 'version': API_VERSION}), 200


def health():
    return jsonify({'status': 'ok', 'timestamp': str(utc_now())}), 200
