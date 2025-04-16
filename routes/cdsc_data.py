from flask import Blueprint, jsonify, request
import logging
import requests
from bs4 import BeautifulSoup
import os
import time

cdsc_data_bp = Blueprint('cdsc_data', __name__)

API_KEY = os.getenv('API_KEY')  # Set this in Render.com env vars

# --- Basic Rate Limiter (in-memory) ---
REQUEST_LOG = {}
MAX_REQUESTS_PER_MINUTE = 10  # You can adjust this

def rate_limit(ip):
    now = time.time()
    window = 60  # 60 seconds
    if ip not in REQUEST_LOG:
        REQUEST_LOG[ip] = [now]
        return False
    REQUEST_LOG[ip] = [ts for ts in REQUEST_LOG[ip] if now - ts < window]
    if len(REQUEST_LOG[ip]) >= MAX_REQUESTS_PER_MINUTE:
        return True
    REQUEST_LOG[ip].append(now)
    return False

# --- API Route ---
@cdsc_data_bp.route('/api/v1/cdsc/data', methods=['GET'])
def get_cdsc_data():
    ip = request.remote_addr

    if rate_limit(ip):
        return jsonify({'success': False, 'message': 'Rate limit exceeded. Try again later.'}), 429

    provided_key = request.headers.get('x-api-key') or request.args.get('api_key')
    if not API_KEY or provided_key != API_KEY:
        return jsonify({'success': False, 'message': 'Unauthorized. Invalid or missing API Key.'}), 401

    try:
        data = scrape_cdsc_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logging.error(f"CDSC fetch error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch CDSC data.'}), 500

def scrape_cdsc_data():
    url = "https://www.cdsc.com.np/"
    response = requests.get(url, verify=False)
    html_content = response.text
    soup = BeautifulSoup(html_content, "html.parser")
    div = soup.find("div", class_="fun-factor-area")
    h4_elements = div.find_all("h4")
    data = []
    important_positions = [8, 10, 11, 12, 13]

    for i in range(0, len(h4_elements), 2):
        imp_value = "true" if int(i / 2) in important_positions else "false"
        item = {
            "id": str(int(i / 2)),
            "dataKey": h4_elements[i + 1].text.strip(),
            "dataValue": h4_elements[i].text.strip(),
            "imp": imp_value
        }
        data.append(item)

    data.sort(key=lambda x: x['imp'], reverse=True)
    return data
