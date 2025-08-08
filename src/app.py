import json
import requests

from flask import Flask, request, Response
from pydantic import ValidationError

from configs.config import API_KEY, API_URL, STRATEGY, PRODUCTS_SIZE
from models import ResponseModel


app = Flask(__name__)


@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return Response(json.dumps({}, ensure_ascii=False), status=400, content_type='application/json')

    url = (
        f"{API_URL}"
        f"?st={query}"
        f"&apiKey={API_KEY}"
        f"&strategy={STRATEGY}"
        f"&productsSize={PRODUCTS_SIZE}"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://shop.kz/"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return Response(json.dumps({}, ensure_ascii=False), status=502, content_type='application/json')

    products = data.get("products", [])

    try:
        validated = ResponseModel(results=products)
    except ValidationError as e:
        return Response(
            e.json(),
            status=422,
            content_type='application/json'
        )

    result_json = json.dumps({"results": products}, ensure_ascii=False, indent=2)
    return Response(result_json, content_type='application/json')
