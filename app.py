from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

def extract_author_name(text):
    ignore_words = {"about", "above", "across", "after", "against", "along", "amid", "among", "around", "at", "before", "behind", "below", "beneath", "beside", "between", "beyond", "but", "by", "concerning", "despite", "down", "during", "except", "for", "from", "in", "inside",  "into", "like", "near", "of", "off", "on", "onto", "out", "outside", "over", "past",  "regarding", "since", "through", "throughout", "to", "toward", "under", "underneath", "until", "up", "upon", "with", "within", "without"}
    words = text.split()
    filtered_words = [word for word in words if word.lower() not in ignore_words]
    author = re.findall(r'\b[A-Z][a-z]*\s[A-Z][a-z]*\b', ' '.join(filtered_words))
    return author

def find_author(soup):
    author_meta = soup.find('meta', attrs={'name': 'author'})
    if author_meta:
        author_content = re.sub('<[^<]+?>', '', author_meta['content'])
        author = extract_author_name(author_content)
        if author:
            return author

    author_div = soup.find(lambda tag: tag.name == "div" and "author" in tag.get('class', []))
    if author_div:
        author_without_tags = re.sub('<[^<]+?>', '', author_div.get_text(strip=True))
        author = extract_author_name(author_without_tags)
        if author:
            return author

    return 'No author found'

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

        author = find_author(soup)

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
