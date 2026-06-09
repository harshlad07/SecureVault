"""Web interface for the local encrypted password vault."""

import os
import socket
from flask import Flask, request, redirect, url_for, render_template_string, flash
from storage.db_manager import DatabaseManager

WEB_STATE = {"key": None}


def create_web_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.urandom(16)
    db = DatabaseManager()

    def _require_login() -> bool:
        return WEB_STATE["key"] is not None

    def _render_template(content: str, **context):
        base_html = """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Secure Password Vault</title>
            <style>
              body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }
              .container { max-width: 900px; margin: 2rem auto; background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
              table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
              th, td { padding: 0.85rem; border-bottom: 1px solid #ddd; text-align: left; }
              input, textarea, select { width: 100%; padding: 0.7rem; margin-top: 0.25rem; margin-bottom: 0.75rem; border: 1px solid #ccc; border-radius: 4px; }
              button { padding: 0.75rem 1.2rem; border: none; border-radius: 4px; background: #0078d4; color: white; cursor: pointer; }
              button.secondary { background: #555; }
              .actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
              .flash { padding: 0.75rem; background: #ffe9b0; border-radius: 4px; margin-bottom: 1rem; }
            </style>
          </head>
          <body>
            <div class="container">
              {{ content | safe }}
            </div>
          </body>
        </html>
        """
        return render_template_string(base_html, content=content, **context)

    @app.route("/", methods=["GET", "POST"])
    def login():
        if db.is_initialized() and request.method == "POST":
            password = request.form.get("password", "")
            key = db.authenticate_master_password(password)
            if key is not None:
                WEB_STATE["key"] = key
                return redirect(url_for("vault"))
            flash("Invalid master password.")
        if not db.is_initialized():
            return redirect(url_for("setup"))
        body = """
        <h1>Secure Password Vault</h1>
        <p>Enter your master password to unlock the local vault.</p>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="post">
          <label>Master Password</label>
          <input name="password" type="password" required>
          <button type="submit">Unlock</button>
        </form>
        """
        return _render_template(body)

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if db.is_initialized():
            return redirect(url_for("login"))
        if request.method == "POST":
            password = request.form.get("password", "")
            confirm = request.form.get("confirm", "")
            if password != confirm:
                flash("Passwords do not match.")
            elif len(password) < 10:
                flash("Master password should be at least 10 characters.")
            else:
                db.setup_master_password(password)
                flash("Master password configured. Please log in.")
                return redirect(url_for("login"))
        body = """
        <h1>Setup Master Password</h1>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="post">
          <label>Master Password</label>
          <input name="password" type="password" required>
          <label>Confirm Password</label>
          <input name="confirm" type="password" required>
          <button type="submit">Create Vault</button>
        </form>
        """
        return _render_template(body)

    @app.route("/vault")
    def vault():
        if not _require_login():
            return redirect(url_for("login"))
        credentials = db.list_credentials(WEB_STATE["key"])
        rows = "".join(
            f"<tr><td>{record['website']}</td><td>{record['username']}</td><td>{record['updated_at']}</td>"
            f"<td class=\"actions\">"
            f"<a href=\"/edit/{record['id']}\"><button>Edit</button></a>"
            f"<a href=\"/delete/{record['id']}\"><button class=\"secondary\">Delete</button></a>"
            f"</td></tr>"
            for record in credentials
        )
        body = f"""
        <h1>Password Vault</h1>
        <p>Access the local vault from this browser. Data remains encrypted on disk.</p>
        <div class=\"actions\"><a href=\"/add\"><button>Add Credential</button></a><a href=\"/logout\"><button class=\"secondary\">Lock</button></a></div>
        <table>
          <thead>
            <tr><th>Website</th><th>Username</th><th>Updated</th><th>Actions</th></tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        """
        return _render_template(body)

    @app.route("/add", methods=["GET", "POST"])
    def add():
        if not _require_login():
            return redirect(url_for("login"))
        if request.method == "POST":
            credential = {
                "website": request.form.get("website", "").strip(),
                "username": request.form.get("username", "").strip(),
                "password": request.form.get("password", ""),
                "notes": request.form.get("notes", "").rstrip("\n"),
            }
            if not credential["website"] or not credential["username"] or not credential["password"]:
                flash("Website, username, and password are required.")
            else:
                db.add_credential(credential, WEB_STATE["key"])
                return redirect(url_for("vault"))
        body = """
        <h1>Add Credential</h1>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="flash">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form method="post">
          <label>Website</label><input name="website" required>
          <label>Username</label><input name="username" required>
          <label>Password</label><input name="password" required>
          <label>Notes</label><textarea name="notes"></textarea>
          <button type="submit">Save</button>
        </form>
        <div class=\"actions\"><a href=\"/vault\"><button class=\"secondary\">Back</button></a></div>
        """
        return _render_template(body)

    @app.route("/edit/<int:record_id>", methods=["GET", "POST"])
    def edit(record_id: int):
        if not _require_login():
            return redirect(url_for("login"))
        credential = db.get_credential(record_id, WEB_STATE["key"])
        if credential is None:
            flash("Credential not found.")
            return redirect(url_for("vault"))
        if request.method == "POST":
            credential["website"] = request.form.get("website", "").strip()
            credential["username"] = request.form.get("username", "").strip()
            credential["password"] = request.form.get("password", "")
            credential["notes"] = request.form.get("notes", "").rstrip("\n")
            if not credential["website"] or not credential["username"] or not credential["password"]:
                flash("Website, username, and password are required.")
            else:
                db.update_credential(record_id, credential, WEB_STATE["key"])
                return redirect(url_for("vault"))
        body = f"""
        <h1>Edit Credential</h1>
        <form method=\"post\">
          <label>Website</label><input name=\"website\" value=\"{credential['website']}\" required>
          <label>Username</label><input name=\"username\" value=\"{credential['username']}\" required>
          <label>Password</label><input name=\"password\" value=\"{credential['password']}\" required>
          <label>Notes</label><textarea name=\"notes\">{credential['notes']}</textarea>
          <button type=\"submit\">Save</button>
        </form>
        <div class=\"actions\"><a href=\"/vault\"><button class=\"secondary\">Back</button></a></div>
        """
        return _render_template(body)

    @app.route("/delete/<int:record_id>")
    def delete(record_id: int):
        if not _require_login():
            return redirect(url_for("login"))
        db.delete_credential(record_id)
        return redirect(url_for("vault"))

    @app.route("/logout")
    def logout():
        WEB_STATE["key"] = None
        return redirect(url_for("login"))

    return app


def start_web_server() -> None:
    app = create_web_app()
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Starting local web vault. Open http://{local_ip}:5000 on your iPhone.")
    app.run(host="0.0.0.0", port=5000)
