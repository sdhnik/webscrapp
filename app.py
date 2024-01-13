from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route('/', methods=['POST'])
def scrape_webpage():
    # Get URL from POST data
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided in the request body"}), 400

    try:
        # Fetch webpage content
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract details
        title = soup.find('title').get_text() if soup.find('title') else 'No title found'

        author = soup.find('meta', attrs={'name': 'author'})['content'] if soup.find('meta', attrs={'name': 'author'}) else None
        if not author:
            author_div = soup.find(lambda tag: tag.name == "div" and "author" in tag.get('class', []))
            author = author_div.get_text(strip=True) if author_div else 'No author found'

        date_created = soup.find('meta', attrs={'property': 'article:published_time'})['content'] if soup.find('meta', attrs={'property': 'article:published_time'}) else None
        if not date_created:
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            date_created = re.search(date_pattern, soup.get_text())
            date_created = date_created.group() if date_created else 'No date found'

        site_name = soup.find('meta', attrs={'property': 'og:site_name'})['content'] if soup.find('meta', attrs={'property': 'og:site_name'}) else None

        return jsonify({"title": title, "siteName": site_name, "author": author, "published": date_created, "url": url})
    except requests.HTTPError as http_err:
        return jsonify({"error": f"HTTP error occurred: {http_err}"}), 500
    except Exception as err:
        return jsonify({"error": f"An error occurred: {err}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
