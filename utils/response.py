from flask import make_response, json


def json_response(data, status_code=200):
    """统一的 JSON 响应处理"""
    return make_response(
        json.dumps(data, ensure_ascii=False, indent=2),
        status_code,
        {'Content-Type': 'application/json; charset=utf-8'}
    )
