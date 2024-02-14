from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)


# Prospectus Data - START
# Source: https://www.sebon.gov.np/prospectus?page={page numbers}
# Request URL: https://hsmmarketdata.onrende.com/get_prospectus/1 or 1,2 or 1,2,3
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
                    # Determine which URL to use for file size calculation
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
# Prospectus Data - END


@app.route('/get_prospectus/<page_numbers>', methods=['GET'])
def get_prospectus(page_numbers):
    page_numbers = [int(page) for page in page_numbers.split(',')]
    data = scrape_sebon_data(page_numbers)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
