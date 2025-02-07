from flask import Flask, request, Response, redirect
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

PROXY_PREFIX = "/proxy/"

def rewrite_links(content, base_url):
    """
    Modify all links in the HTML so they pass through the proxy.
    """
    soup = BeautifulSoup(content, "html.parser")

    for tag in soup.find_all(["a", "link", "script", "img", "form"]):
        attr = "href" if tag.name in ["a", "link"] else "src" if tag.name in ["script", "img"] else None

        if attr and tag.has_attr(attr):
            tag[attr] = urljoin(base_url, f"{PROXY_PREFIX}?url={tag[attr]}")

        if tag.name == "form" and tag.has_attr("action"):
            tag["action"] = urljoin(base_url, f"{PROXY_PREFIX}?url={tag['action']}")

    return str(soup)

@app.route('/')
def home():
    return '''
        <h2>Enter a URL to browse:</h2>
        <form action="/proxy/" method="get">
            <input type="text" name="url" placeholder="https://example.com" required>
            <button type="submit">Go</button>
        </form>
    '''

@app.route(PROXY_PREFIX, methods=["GET", "POST"])
def proxy():
    target_url = request.args.get('url') or request.form.get('url')
    if not target_url:
        return "Error: No URL provided.", 400

    try:
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}

        # Handle GET and POST requests
        if request.method == "POST":
            response = requests.post(target_url, data=request.form, headers=headers, allow_redirects=True, stream=True)
        else:
            response = requests.get(target_url, headers=headers, allow_redirects=True, stream=True)

        content_type = response.headers.get('Content-Type', '')

        if "text/html" in content_type:
            modified_content = rewrite_links(response.text, request.url)
            return Response(modified_content, content_type=content_type)

        return Response(response.raw, content_type=content_type)

    except requests.RequestException as e:
        return f"Error fetching page: {e}", 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
