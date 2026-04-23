"""
Helper OAuth: abre o Jobber no browser, captura o callback,
troca o code por um novo refresh_token e atualiza config.py.

Antes de rodar:
1. Acesse https://developer.getjobber.com/apps/MTU0NTk3
2. Em "Redirect URIs" adicione: http://localhost:8765/callback
3. Salve e rode: python get_new_token.py
"""

import http.server
import socketserver
import urllib.parse
import webbrowser
import requests
import re
import sys
from pathlib import Path

from config import JOBBER_CLIENT_ID, JOBBER_CLIENT_SECRET, JOBBER_TOKEN_URL

PORT = 8765
REDIRECT_URI = f"http://localhost:{PORT}/callback"
AUTH_URL = "https://api.getjobber.com/api/oauth/authorize"
SCOPES = "read_clients read_quotes read_jobs read_invoices read_line_items"

captured_code = {"value": None, "error": None}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/callback":
            if "code" in params:
                captured_code["value"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Authorized</h1><p>You can close this tab.</p>")
            else:
                captured_code["error"] = params.get("error", ["unknown"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>Error: {captured_code['error']}</h1>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_):
        pass


def update_config(new_refresh_token: str):
    config_path = Path(__file__).parent / "config.py"
    text = config_path.read_text()
    new_text = re.sub(
        r'JOBBER_REFRESH_TOKEN\s*=\s*"[^"]*"',
        f'JOBBER_REFRESH_TOKEN = "{new_refresh_token}"',
        text,
    )
    config_path.write_text(new_text)


def main():
    auth_params = {
        "client_id":     JOBBER_CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         SCOPES,
    }
    full_auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"

    print(f"\nAbrindo browser para autorizar...")
    print(f"Se nao abrir, acesse manualmente:\n{full_auth_url}\n")
    webbrowser.open(full_auth_url)

    with socketserver.TCPServer(("", PORT), CallbackHandler) as httpd:
        print(f"Aguardando callback em {REDIRECT_URI}...")
        while captured_code["value"] is None and captured_code["error"] is None:
            httpd.handle_request()

    if captured_code["error"]:
        print(f"\nErro OAuth: {captured_code['error']}")
        sys.exit(1)

    code = captured_code["value"]
    print(f"\nCode recebido. Trocando por tokens...")

    resp = requests.post(JOBBER_TOKEN_URL, data={
        "client_id":     JOBBER_CLIENT_ID,
        "client_secret": JOBBER_CLIENT_SECRET,
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
    })

    if resp.status_code != 200:
        print(f"\nFalha: {resp.status_code}\n{resp.text}")
        sys.exit(1)

    data = resp.json()
    new_refresh = data.get("refresh_token")

    if not new_refresh:
        print(f"\nResposta sem refresh_token:\n{data}")
        sys.exit(1)

    update_config(new_refresh)
    print(f"\nconfig.py atualizado com novo refresh_token.")
    print(f"   (primeiros 8 chars: {new_refresh[:8]}...)")


if __name__ == "__main__":
    main()
