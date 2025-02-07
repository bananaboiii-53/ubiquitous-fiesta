from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

PROXY_PREFIX = "/proxy/"

@app.route('/')
def home():
    return '''
        <h2>Enter a URL to browse:</h2>
        <form action="/proxy/" method="get">
            <input type="text" name="url" placeholder="https://example.com">
            <button type="submit">Go</button>
        </form>
    '''

@app.route(PROXY_PREFIX)
def proxy():
    target_url = request.args.get('url')
    if not target_url:
        return "Error: No URL provided.", 400

    try:
        # Fetch the requested page
        response = requests.get(target_url)
        response.raise_for_status()
        content = response.text

        # Rewrite links to go through the proxy
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all(["a", "link", "script"]):
            attr = "href" if tag.name != "script" else "src"
            if tag.has_attr(attr):
                tag[attr] = urljoin(request.url, f"{PROXY_PREFIX}?url={tag[attr]}")

        modified_content = str(soup)

        return Response(modified_content, content_type=response.headers.get('Content-Type', 'text/html'))
    
    except requests.RequestException as e:
        return f"Error fetching page: {e}", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
