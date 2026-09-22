"""Controller de relatórios."""
from flask import jsonify

from services import report_service, user_service


def summary_report():
    return jsonify(report_service.build_summary()), 200


def user_report(user_id: int):
    user = user_service.get_user(user_id)
    return jsonify(report_service.build_user_report(user)), 200
