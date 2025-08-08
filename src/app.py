import json
import requests

from flask import Flask, request, Response
from pydantic import ValidationError

from configs.config import API_KEY, API_URL, STRATEGY, PRODUCTS_SIZE
from models import ResponseModel
from database import db_manager


app = Flask(__name__)


def validate_query(query):
    if not query:
        return False, create_error_response({}, 400)
    return True, None


def build_api_url(query):
    return (
        f"{API_URL}"
        f"?st={query}"
        f"&apiKey={API_KEY}"
        f"&strategy={STRATEGY}"
        f"&productsSize={PRODUCTS_SIZE}"
    )


def get_api_headers():
    return {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://shop.kz/"
    }


def fetch_api_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, create_error_response({"error": str(e)}, 502)


def validate_response_data(data):
    products = data.get("products", [])
    try:
        validated = ResponseModel(results=products)
        return True, products, None
    except ValidationError as e:
        return False, None, Response(
            e.json(),
            status=422,
            content_type='application/json'
        )


def create_success_response(data):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json'
    )


def create_error_response(data, status_code):
    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        status=status_code,
        content_type='application/json'
    )


@app.route('/search')
def search():
    query = request.args.get('q')
    is_valid, error_response = validate_query(query)
    if not is_valid:
        return error_response

    url = build_api_url(query)
    headers = get_api_headers()

    success, api_response = fetch_api_data(url, headers)
    if not success:
        return api_response

    is_valid, products, error_response = validate_response_data(api_response)
    if not is_valid:
        return error_response

    try:
        db_manager.save(query, products)
    except Exception as e:
        print(f"Ошибка сохранения в БД: {e}")

    return create_success_response({"results": products})


@app.route('/history')
def get_search_history():
    try:
        limit = request.args.get('limit', default=10, type=int)
        history = db_manager.get_search_history(limit)
        return create_success_response({"history": history})
    except Exception as e:
        return create_error_response({"error": str(e)}, 500)


@app.route('/products/<int:query_id>')
def get_products_by_query_id(query_id):
    try:
        products = db_manager.get_products_by_query_id(query_id)
        return create_success_response({"results": products})
    except Exception as e:
        return create_error_response({"error": str(e)}, 500)


@app.route('/products/search/<query_text>')
def get_products_by_query_text(query_text):
    try:
        products = db_manager.get_products_by_query_text(query_text)
        return create_success_response({"results": products})
    except Exception as e:
        return create_error_response({"error": str(e)}, 500)


@app.route('/statistics')
def get_statistics():
    try:
        stats = db_manager.get_statistics()
        return create_success_response(stats)
    except Exception as e:
        return create_error_response({"error": str(e)}, 500)
