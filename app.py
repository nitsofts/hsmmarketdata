from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)

# Define the path where the prospectus.json file will be saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Gets the directory where the script runs
PROSPECTUS_FILE_PATH = os.path.join(BASE_DIR, 'hsmmarketdata', 'response', 'prospectus.json')

def get_file_size(url):
    try:
        response = requests.head(url)
        file_size_bytes = int(response.headers.get('content-length', 0))
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)  # Convert bytes to MB
        return file_size_mb
    except Exception:
        return "N/A"  # Return "N/A" if size can't be calculated

def scrape_sebon_data(page_numbers):
    combined_data = []

    for page_number in page_numbers:
        url = f"https://www.sebon.gov.np/prospectus?page={page_number}"
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='table')
            table_rows = table.select('tbody tr')
            data_list = []

            for row in table_rows:
                row_data = row.find_all('td')
                if len(row_data) == 4:
                    file_url = row_data[3].find('a').get('href', '') if row_data[3].find('a') else row_data[2].find('a').get('href', '')
                    file_size = get_file_size(file_url) if file_url else "N/A"

                    data = {
                        "title": row_data[0].get_text(strip=True),
                        "date": row_data[1].get_text(strip=True),
                        "english": row_data[2].find('a').get('href', '') if row_data[2].find('a') else '',
                        "nepali": row_data[3].find('a').get('href', '') if row_data[3].find('a') else '',
                        "fileSize": file_size
                    }
                    data_list.append(data)

            combined_data.extend(data_list)
        else:
            print(f"Failed to retrieve page {page_number}. Status code:", response.status_code)

    return combined_data

@app.route('/get_prospectus/<page_numbers>', methods=['GET'])
def get_prospectus(page_numbers):
    page_numbers = [int(page) for page in page_numbers.split(',')]
    data = scrape_sebon_data(page_numbers)
    
    # Write data to the prospectus.json file
    os.makedirs(os.path.dirname(PROSPECTUS_FILE_PATH), exist_ok=True)  # Create directories if they don't exist
    with open(PROSPECTUS_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
