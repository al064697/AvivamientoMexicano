import json, os, re, uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.request import Request, urlopen

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "datos.json"
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-this-secret")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
REGISTRATION_FIELD_LABELS = {
    "full_name": "Nombre completo",
    "age": "Edad",
    "sex": "Sexo",
    "phone": "Teléfono",
    "email": "Email",
    "location": "Ciudad / Estado",
    "church": "Iglesia",
    "church_location": "Ciudad de iglesia",
    "pastor": "Pastor principal",
    "ministry": "Ministerio",
    "consent": "Consentimiento",
    "id": "ID del registro",
    "created_at": "Fecha de registro",
    "status": "Estado"
}
REGISTRATION_FIELD_ORDER = list(REGISTRATION_FIELD_LABELS)


def load_data():
    if not DATA_FILE.exists():
        return {"admin": {"username": "admin"}, "registrations": []}
    with DATA_FILE.open("r", encoding="utf-8") as data_file:
        return json.load(data_file)


def save_data(data):
    temporary_file = DATA_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as data_file:
        json.dump(data, data_file, ensure_ascii=False, indent=2)
    temporary_file.replace(DATA_FILE)


def supabase_enabled():
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def supabase_request(resource, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{SUPABASE_URL}/rest/v1/{resource}",
        data=body,
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        },
        method=method
    )
    with urlopen(request, timeout=10) as response:
        response_body = response.read()
        return json.loads(response_body) if response_body else None


def supabase_admin():
    records = supabase_request("admins?select=username,password_hash&limit=1")
    return records[0] if records else None


def get_registrations():
    if supabase_enabled():
        return supabase_request("registrations?select=*&order=created_at.desc") or []
    return list(reversed(load_data().get("registrations", [])))


def admin_is_configured(data=None):
    admin = (data or (supabase_admin() if supabase_enabled() else load_data().get("admin", {})))
    return bool(admin.get("username") and admin.get("password_hash"))


def admin_password_is_valid(password):
    admin = supabase_admin() if supabase_enabled() else load_data().get("admin", {})
    password_hash = admin.get("password_hash")
    return bool(password_hash and check_password_hash(password_hash, password))


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not admin_is_configured():
            return redirect(url_for("admin_setup"))
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def clean(value):
    return str(value or "").strip()


def registration_value(value, field):
    if field == "consent":
        return "Sí" if str(value).lower() == "true" else "No"
    return value or "-"


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/registro")
def registration_page():
    return render_template("registro.html")


@app.post("/api/registro")
def create_registration():
    payload = request.get_json(silent=True) or request.form
    required_fields = [
        "full_name", "age", "sex", "phone", "email", "location",
        "church", "church_location", "pastor", "ministry", "consent"
    ]
    registration = {field: clean(payload.get(field)) for field in required_fields}

    missing_fields = [field for field in required_fields if not registration[field]]
    if missing_fields:
        return jsonify(error="Completa todos los campos del registro."), 400

    try:
        registration["age"] = int(registration["age"])
    except ValueError:
        return jsonify(error="La edad debe ser un número válido."), 400

    if not 1 <= registration["age"] <= 120:
        return jsonify(error="La edad debe estar entre 1 y 120 años."), 400
    if registration["consent"].lower() != "true":
        return jsonify(error="Debes aceptar recibir información del congreso."), 400
    if registration["sex"] not in {"Mujer", "Hombre"}:
        return jsonify(error="Selecciona una opción válida para sexo."), 400
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", registration["email"]):
        return jsonify(error="Escribe un correo electrónico válido."), 400

    existing_registrations = get_registrations()
    email_exists = any(
        item.get("email", "").lower() == registration["email"].lower()
        for item in existing_registrations
    )
    if email_exists:
        return jsonify(error="Este correo ya tiene un registro."), 409

    registration.update({
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "registered"
    })
    if supabase_enabled():
        supabase_request("registrations", method="POST", payload=registration)
    else:
        data = load_data()
        data.setdefault("registrations", []).append(registration)
        save_data(data)
    return jsonify(message="Registro completado."), 201


@app.route("/admin/configurar", methods=["GET", "POST"])
def admin_setup():
    if admin_is_configured():
        return redirect(url_for("admin_login"))

    error = None
    if request.method == "POST":
        username = clean(request.form.get("username"))
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")
        if len(username) < 3:
            error = "El usuario debe tener al menos 3 caracteres."
        elif len(password) < 8:
            error = "La contraseña debe tener al menos 8 caracteres."
        elif password != confirmation:
            error = "Las contraseñas no coinciden."
        else:
            admin = {
                "username": username,
                "password_hash": generate_password_hash(password)
            }
            if supabase_enabled():
                supabase_request("admins", method="POST", payload=admin)
            else:
                data = load_data()
                data["admin"] = admin
                save_data(data)
            session["admin_authenticated"] = True
            return redirect(url_for("admin_dashboard"))
    return render_template("admin_setup.html", error=error)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if not admin_is_configured():
        return redirect(url_for("admin_setup"))

    error = None
    if request.method == "POST":
        username = clean(request.form.get("username"))
        password = request.form.get("password", "")
        admin = supabase_admin() if supabase_enabled() else load_data().get("admin", {})
        admin_username = admin.get("username", "admin")
        if username == admin_username and admin_password_is_valid(password):
            session["admin_authenticated"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Usuario o contraseña incorrectos."
    return render_template("login.html", error=error)


@app.get("/login")
def login():
    return redirect(url_for("admin_login"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    registrations = get_registrations()
    existing_fields = {field for person in registrations for field in person}
    ordered_fields = [field for field in REGISTRATION_FIELD_ORDER if field in existing_fields]
    additional_fields = sorted(existing_fields.difference(ordered_fields))
    registration_fields = ordered_fields + additional_fields
    field_labels = {
        field: REGISTRATION_FIELD_LABELS.get(field, field.replace("_", " ").title())
        for field in registration_fields
    }
    return render_template(
        "admin.html",
        registrations=registrations,
        registration_fields=registration_fields,
        field_labels=field_labels,
        registration_value=registration_value
    )


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", 5000)))