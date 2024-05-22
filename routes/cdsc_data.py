from flask import Blueprint, jsonify
import logging
import requests
from bs4 import BeautifulSoup

cdsc_data_bp = Blueprint('cdsc_data', __name__)

@cdsc_data_bp.route('/get_cdsc_data', methods=['GET'])
def get_cdsc_data():
    try:
        data = scrape_cdsc_data()
        return jsonify(data)
    except Exception as e:
        logging.error(f"An error occurred while fetching CDSC data: {str(e)}")
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
        imp_value = "true" if int(i/2) in important_positions else "false"
        item = {
            "id": str(int(i/2)),
            "dataKey": h4_elements[i + 1].text.strip(),
            "dataValue": h4_elements[i].text.strip(),
            "imp": imp_value
        }
        data.append(item)

    data.sort(key=lambda x: x['imp'], reverse=True)
    
    return data
