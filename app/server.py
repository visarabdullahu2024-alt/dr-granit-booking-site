#!/usr/bin/env python3
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import sqlite3
import uuid
from datetime import date, datetime, time, timedelta, timezone
from email.message import EmailMessage
from http import cookies
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DOCTOR_APP_DB_PATH", str(ROOT / "doctor_booking.db")))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
HOST = os.getenv("DOCTOR_APP_HOST", "127.0.0.1")
PORT = int(os.getenv("PORT") or os.getenv("DOCTOR_APP_PORT", "8000"))
CORS_ORIGIN = os.getenv("DOCTOR_APP_CORS_ORIGIN", "*")
SESSION_COOKIE = "doctor_booking_session"
EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
SESSIONS = {}
USE_POSTGRES = bool(DATABASE_URL)

APP_CONFIG = {
    "doctorName": "Dr. Granit Abdullahu",
    "doctorTitle": "Thoracic Surgeon",
    "doctorBio": (
        "Specialized thoracic surgery care with a calm, direct booking experience for"
        " consultations, follow-up visits, and second opinions."
    ),
    "doctorEmail": os.getenv("DOCTOR_PUBLIC_EMAIL", "dr.granit@hotmail.com"),
    "doctorPhone": os.getenv("DOCTOR_NOTIFICATION_PHONE", "044960003"),
    "notificationEmail": os.getenv("DOCTOR_NOTIFICATION_EMAIL", "visar.abdullahu@gmail.com"),
    "doctorPassword": os.getenv("DOCTOR_DASHBOARD_PASSWORD", "Doctor123!"),
    "timezoneLabel": "Europe/Belgrade",
}

PROFILE = {
    "name": APP_CONFIG["doctorName"],
    "title": APP_CONFIG["doctorTitle"],
    "bio": APP_CONFIG["doctorBio"],
    "phone": APP_CONFIG["doctorPhone"],
    "email": APP_CONFIG["doctorEmail"],
    "yearsExperience": "15+ years",
    "highlights": [
        "Thoracic consultations and diagnosis review",
        "Pre-operative planning and surgical second opinions",
        "Post-operative follow-up and recovery monitoring",
    ],
}

SEED_SERVICES = [
    {
        "name": "Thoracic Consultation",
        "description": "Initial consultation for chest, lung, pleural, and thoracic surgical concerns.",
        "duration_minutes": 45,
        "price_label": "By request",
    },
    {
        "name": "Second Opinion Review",
        "description": "Review imaging, reports, and treatment recommendations with a specialist perspective.",
        "duration_minutes": 60,
        "price_label": "By request",
    },
    {
        "name": "Follow-Up Visit",
        "description": "Post-operative follow-up, recovery check, or ongoing thoracic care review.",
        "duration_minutes": 30,
        "price_label": "By request",
    },
    {
        "name": "Surgery Booking",
        "description": "Pre-surgery planning, booking request, and coordination for thoracic surgical procedures.",
        "duration_minutes": 60,
        "price_label": "By request",
    },
]

SEED_LOCATIONS = [
    {
        "name": "Prishtina Clinic",
        "address": "Mother Teresa Street, Prishtina",
        "details": "Primary consultation location for weekday appointments.",
    },
    {
        "name": "Ferizaj Medical Center",
        "address": "Driton Islami Avenue, Ferizaj",
        "details": "Selected follow-up and consultation sessions.",
    },
    {
        "name": "Gjilan Specialist Office",
        "address": "City Center, Gjilan",
        "details": "Limited monthly thoracic consultation sessions.",
    },
]

SEED_AVAILABILITY = [
    {"location_name": "Prishtina Clinic", "day_of_week": 0, "start_time": "09:00", "end_time": "14:00"},
    {"location_name": "Prishtina Clinic", "day_of_week": 2, "start_time": "09:00", "end_time": "16:00"},
    {"location_name": "Prishtina Clinic", "day_of_week": 4, "start_time": "09:00", "end_time": "14:00"},
    {"location_name": "Ferizaj Medical Center", "day_of_week": 1, "start_time": "13:00", "end_time": "18:00"},
    {"location_name": "Gjilan Specialist Office", "day_of_week": 3, "start_time": "10:00", "end_time": "15:00"},
]


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(value: str) -> str:
    return (value or "").strip()


def valid_email(value: str) -> bool:
    return bool(value and re.match(EMAIL_RE, value.strip()))


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return digest.hex()


def make_password_record(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    return salt, hash_password(password, salt)


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password, salt), password_hash)


def parse_iso_datetime(value: str) -> datetime:
    text = normalize_text(value)
    if not text:
        raise ValueError("datetime is required")
    try:
        if text.endswith("Z"):
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        else:
            parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("Invalid datetime format.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def parse_local_time(value: str) -> time:
    cleaned = normalize_text(value)
    try:
        hour, minute = cleaned.split(":")
        parsed = time(hour=int(hour), minute=int(minute))
    except (ValueError, AttributeError) as exc:
        raise ValueError("Time must be in HH:MM format.") from exc
    return parsed


def format_day_label(day_index: int) -> str:
    labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return labels[day_index]


class DBConnection:
    def __init__(self, raw_conn, use_postgres: bool):
        self.raw_conn = raw_conn
        self.use_postgres = use_postgres

    def execute(self, sql: str, params=()):
        if self.use_postgres:
            return self.raw_conn.execute(sql.replace("?", "%s"), params)
        return self.raw_conn.execute(sql, params)

    def executescript(self, script: str):
        if self.use_postgres:
            statements = [part.strip() for part in script.split(";") if part.strip()]
            for statement in statements:
                self.raw_conn.execute(statement)
            return None
        return self.raw_conn.executescript(script)

    def commit(self):
        return self.raw_conn.commit()

    def close(self):
        return self.raw_conn.close()


def db_conn():
    if USE_POSTGRES:
        if psycopg is None:
            raise RuntimeError("DATABASE_URL is set but psycopg is not installed.")
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return DBConnection(conn, True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return DBConnection(conn, False)


def init_db():
    conn = db_conn()
    if not USE_POSTGRES:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS doctor_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                price_label TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                details TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weekly_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                day_of_week INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                FOREIGN KEY(location_id) REFERENCES locations(id)
            );

            CREATE TABLE IF NOT EXISTS schedule_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(location_id) REFERENCES locations(id)
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                patient_email TEXT NOT NULL,
                patient_phone TEXT,
                reason TEXT NOT NULL,
                service_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                appointment_at TEXT NOT NULL,
                appointment_end_at TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(service_id) REFERENCES services(id),
                FOREIGN KEY(location_id) REFERENCES locations(id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(booking_id) REFERENCES bookings(id)
            );
            """
        )
    else:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS doctor_accounts (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS services (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                price_label TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS locations (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                address TEXT NOT NULL,
                details TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weekly_availability (
                id BIGSERIAL PRIMARY KEY,
                location_id BIGINT NOT NULL REFERENCES locations(id),
                day_of_week INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schedule_locks (
                id BIGSERIAL PRIMARY KEY,
                location_id BIGINT REFERENCES locations(id),
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id BIGSERIAL PRIMARY KEY,
                patient_name TEXT NOT NULL,
                patient_email TEXT NOT NULL,
                patient_phone TEXT,
                reason TEXT NOT NULL,
                service_id BIGINT NOT NULL REFERENCES services(id),
                location_id BIGINT NOT NULL REFERENCES locations(id),
                appointment_at TEXT NOT NULL,
                appointment_end_at TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,
                booking_id BIGINT REFERENCES bookings(id),
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )

    seeded_email = "doctor@granitabdullahu.local"
    existing = conn.execute("SELECT id FROM doctor_accounts WHERE email = ?", (seeded_email,)).fetchone()
    if not existing:
        salt, password_hash = make_password_record(APP_CONFIG["doctorPassword"])
        conn.execute(
            """
            INSERT INTO doctor_accounts (name, email, password_salt, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (PROFILE["name"], seeded_email, salt, password_hash, utc_now_iso()),
        )

    for service in SEED_SERVICES:
        conn.execute(
            """
            INSERT INTO services (name, description, duration_minutes, price_label)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                description = excluded.description,
                duration_minutes = excluded.duration_minutes,
                price_label = excluded.price_label
            """,
            (service["name"], service["description"], service["duration_minutes"], service["price_label"]),
        )

    for location in SEED_LOCATIONS:
        conn.execute(
            """
            INSERT INTO locations (name, address, details)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                address = excluded.address,
                details = excluded.details
            """,
            (location["name"], location["address"], location["details"]),
        )

    if conn.execute("SELECT COUNT(*) AS count FROM weekly_availability").fetchone()["count"] == 0:
        location_map = {
            row["name"]: row["id"] for row in conn.execute("SELECT id, name FROM locations").fetchall()
        }
        for item in SEED_AVAILABILITY:
            conn.execute(
                """
                INSERT INTO weekly_availability (location_id, day_of_week, start_time, end_time)
                VALUES (?, ?, ?, ?)
                """,
                (
                    location_map[item["location_name"]],
                    item["day_of_week"],
                    item["start_time"],
                    item["end_time"],
                ),
            )

    conn.commit()
    conn.close()


def serialize_service(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "durationMinutes": row["duration_minutes"],
        "priceLabel": row["price_label"],
    }


def serialize_location(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "address": row["address"],
        "details": row["details"],
    }


def serialize_booking(row):
    return {
        "id": row["id"],
        "patientName": row["patient_name"],
        "patientEmail": row["patient_email"],
        "patientPhone": row["patient_phone"],
        "reason": row["reason"],
        "serviceId": row["service_id"],
        "serviceName": row["service_name"],
        "locationId": row["location_id"],
        "locationName": row["location_name"],
        "appointmentAt": row["appointment_at"],
        "appointmentEndAt": row["appointment_end_at"],
        "status": row["status"],
        "createdAt": row["created_at"],
    }


def serialize_lock(row):
    return {
        "id": row["id"],
        "locationId": row["location_id"],
        "locationName": row["location_name"],
        "startAt": row["start_at"],
        "endAt": row["end_at"],
        "note": row["note"],
        "createdAt": row["created_at"],
    }


def serialize_notification(row):
    return {
        "id": row["id"],
        "bookingId": row["booking_id"],
        "kind": row["kind"],
        "title": row["title"],
        "message": row["message"],
        "isRead": bool(row["is_read"]),
        "createdAt": row["created_at"],
    }


def fetch_services(conn):
    rows = conn.execute("SELECT * FROM services ORDER BY duration_minutes ASC, id ASC").fetchall()
    return [serialize_service(row) for row in rows]


def fetch_locations(conn):
    rows = conn.execute("SELECT * FROM locations ORDER BY name ASC").fetchall()
    return [serialize_location(row) for row in rows]


def fetch_weekly_schedule(conn):
    rows = conn.execute(
        """
        SELECT wa.*, l.name AS location_name
        FROM weekly_availability wa
        JOIN locations l ON l.id = wa.location_id
        ORDER BY wa.day_of_week ASC, wa.start_time ASC
        """
    ).fetchall()
    return [
        {
            "id": row["id"],
            "locationId": row["location_id"],
            "locationName": row["location_name"],
            "dayOfWeek": row["day_of_week"],
            "dayLabel": format_day_label(row["day_of_week"]),
            "startTime": row["start_time"],
            "endTime": row["end_time"],
        }
        for row in rows
    ]


def fetch_locks(conn):
    rows = conn.execute(
        """
        SELECT sl.*, l.name AS location_name
        FROM schedule_locks sl
        LEFT JOIN locations l ON l.id = sl.location_id
        ORDER BY sl.start_at ASC
        """
    ).fetchall()
    return [serialize_lock(row) for row in rows]


def fetch_bookings(conn):
    rows = conn.execute(
        """
        SELECT b.*, s.name AS service_name, l.name AS location_name
        FROM bookings b
        JOIN services s ON s.id = b.service_id
        JOIN locations l ON l.id = b.location_id
        ORDER BY b.appointment_at ASC, b.created_at DESC
        """
    ).fetchall()
    return [serialize_booking(row) for row in rows]


def fetch_notifications(conn, limit=20):
    rows = conn.execute(
        """
        SELECT *
        FROM notifications
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [serialize_notification(row) for row in rows]


def location_exists(conn, location_id: int) -> bool:
    row = conn.execute("SELECT id FROM locations WHERE id = ?", (location_id,)).fetchone()
    return bool(row)


def service_row(conn, service_id: int):
    return conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()


def generate_slots(conn, service_id: int, location_id: int, days: int = 21):
    service = service_row(conn, service_id)
    if not service:
        raise ValueError("Selected service was not found.")
    if not location_exists(conn, location_id):
        raise ValueError("Selected location was not found.")

    duration = int(service["duration_minutes"])
    schedule_rows = conn.execute(
        """
        SELECT *
        FROM weekly_availability
        WHERE location_id = ?
        ORDER BY day_of_week ASC, start_time ASC
        """,
        (location_id,),
    ).fetchall()
    bookings = conn.execute(
        """
        SELECT appointment_at, appointment_end_at
        FROM bookings
        WHERE location_id = ?
          AND status IN ('pending', 'confirmed')
        """,
        (location_id,),
    ).fetchall()
    locks = conn.execute(
        """
        SELECT start_at, end_at
        FROM schedule_locks
        WHERE location_id IS NULL OR location_id = ?
        """,
        (location_id,),
    ).fetchall()

    booking_ranges = [
        (parse_iso_datetime(row["appointment_at"]), parse_iso_datetime(row["appointment_end_at"])) for row in bookings
    ]
    lock_ranges = [(parse_iso_datetime(row["start_at"]), parse_iso_datetime(row["end_at"])) for row in locks]

    slots = []
    today = datetime.now(timezone.utc).date()
    now = datetime.now(timezone.utc)
    latest_date = today + timedelta(days=days)
    for offset in range((latest_date - today).days + 1):
        current_date = today + timedelta(days=offset)
        weekday = current_date.weekday()
        day_schedules = [row for row in schedule_rows if row["day_of_week"] == weekday]
        for schedule in day_schedules:
            window_start = datetime.combine(current_date, parse_local_time(schedule["start_time"]), tzinfo=timezone.utc)
            window_end = datetime.combine(current_date, parse_local_time(schedule["end_time"]), tzinfo=timezone.utc)
            cursor = window_start
            while cursor + timedelta(minutes=duration) <= window_end:
                slot_end = cursor + timedelta(minutes=duration)
                if cursor >= now + timedelta(hours=2):
                    overlaps_booking = any(cursor < booked_end and slot_end > booked_start for booked_start, booked_end in booking_ranges)
                    overlaps_lock = any(cursor < lock_end and slot_end > lock_start for lock_start, lock_end in lock_ranges)
                    if not overlaps_booking and not overlaps_lock:
                        slots.append(
                            {
                                "startAt": cursor.isoformat().replace("+00:00", "Z"),
                                "endAt": slot_end.isoformat().replace("+00:00", "Z"),
                                "label": cursor.strftime("%a, %d %b • %H:%M"),
                            }
                        )
                cursor += timedelta(minutes=duration)
    return slots[:30]


def create_notification(conn, booking_id: int, kind: str, title: str, message: str):
    conn.execute(
        """
        INSERT INTO notifications (booking_id, kind, title, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (booking_id, kind, title, message, utc_now_iso()),
    )


def send_booking_email(booking):
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    port = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("SMTP_FROM_EMAIL", username or APP_CONFIG["doctorEmail"])
    recipient = APP_CONFIG["notificationEmail"]
    if not host or not sender or not recipient:
        return False, "SMTP is not configured."

    message = EmailMessage()
    message["Subject"] = f"New appointment booking for {PROFILE['name']}"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "\n".join(
            [
                f"Patient: {booking['patientName']}",
                f"Email: {booking['patientEmail']}",
                f"Phone: {booking['patientPhone'] or 'Not provided'}",
                f"Service: {booking['serviceName']}",
                f"Location: {booking['locationName']}",
                f"Appointment: {booking['appointmentAt']}",
                f"Reason: {booking['reason']}",
            ]
        )
    )

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    except Exception as exc:
        return False, str(exc)
    return True, None


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", CORS_ORIGIN)
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def _json(self, status, payload, headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        content_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_len) if content_len > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _session_token(self):
        raw_cookie = self.headers.get("Cookie")
        if not raw_cookie:
            return None
        jar = cookies.SimpleCookie()
        jar.load(raw_cookie)
        morsel = jar.get(SESSION_COOKIE)
        return morsel.value if morsel else None

    def _current_doctor(self):
        token = self._session_token()
        if not token:
            return None
        return SESSIONS.get(token)

    def _require_auth(self):
        doctor = self._current_doctor()
        if doctor:
            return doctor
        self._json(401, {"error": "Doctor authentication required."})
        return None

    def _lock_id_from_path(self, path: str):
        prefix = "/api/doctor/locks/"
        if not path.startswith(prefix):
            return None
        tail = path[len(prefix):].strip("/")
        if not tail.isdigit():
            return None
        return int(tail)

    def _booking_id_from_status_path(self, path: str):
        prefix = "/api/doctor/bookings/"
        suffix = "/status"
        if not path.startswith(prefix) or not path.endswith(suffix):
            return None
        tail = path[len(prefix):-len(suffix)].strip("/")
        if not tail.isdigit():
            return None
        return int(tail)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/health":
            return self._json(200, {"ok": True, "time": utc_now_iso()})

        if path == "/api/public/config":
            conn = db_conn()
            payload = {
                "profile": PROFILE,
                "services": fetch_services(conn),
                "locations": fetch_locations(conn),
                "schedule": fetch_weekly_schedule(conn),
            }
            conn.close()
            return self._json(200, payload)

        if path == "/api/public/slots":
            service_value = normalize_text((query.get("serviceId") or [""])[0])
            location_value = normalize_text((query.get("locationId") or [""])[0])
            if not service_value.isdigit() or not location_value.isdigit():
                return self._json(400, {"error": "serviceId and locationId are required."})
            conn = db_conn()
            try:
                slots = generate_slots(conn, int(service_value), int(location_value))
            except ValueError as exc:
                conn.close()
                return self._json(400, {"error": str(exc)})
            conn.close()
            return self._json(200, {"slots": slots})

        if path == "/api/doctor/me":
            doctor = self._current_doctor()
            if not doctor:
                return self._json(401, {"error": "Doctor authentication required."})
            conn = db_conn()
            payload = {
                "doctor": doctor,
                "bookings": fetch_bookings(conn),
                "locks": fetch_locks(conn),
                "notifications": fetch_notifications(conn),
                "locations": fetch_locations(conn),
                "schedule": fetch_weekly_schedule(conn),
                "services": fetch_services(conn),
            }
            conn.close()
            return self._json(200, payload)

        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            data = self._read_json()
        except json.JSONDecodeError:
            return self._json(400, {"error": "Invalid JSON payload."})

        if path == "/api/public/bookings":
            patient_name = normalize_text(data.get("patientName"))
            patient_email = normalize_text(data.get("patientEmail")).lower()
            patient_phone = normalize_text(data.get("patientPhone"))
            reason = normalize_text(data.get("reason"))
            slot_value = normalize_text(data.get("slot"))
            service_value = normalize_text(str(data.get("serviceId", "")))
            location_value = normalize_text(str(data.get("locationId", "")))

            missing = [
                field
                for field, value in {
                    "patientName": patient_name,
                    "patientEmail": patient_email,
                    "reason": reason,
                    "slot": slot_value,
                    "serviceId": service_value,
                    "locationId": location_value,
                }.items()
                if not value
            ]
            if missing:
                return self._json(400, {"error": f"Missing fields: {', '.join(missing)}"})
            if not valid_email(patient_email):
                return self._json(400, {"error": "Please enter a valid email address."})
            if not service_value.isdigit() or not location_value.isdigit():
                return self._json(400, {"error": "Invalid service or location selection."})

            try:
                appointment_at = parse_iso_datetime(slot_value)
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            conn = db_conn()
            try:
                service = service_row(conn, int(service_value))
                if not service:
                    raise ValueError("Selected service was not found.")
                if not location_exists(conn, int(location_value)):
                    raise ValueError("Selected location was not found.")
                available_slots = generate_slots(conn, int(service_value), int(location_value))
                if appointment_at.isoformat().replace("+00:00", "Z") not in {slot["startAt"] for slot in available_slots}:
                    raise ValueError("That appointment slot is no longer available.")
            except ValueError as exc:
                conn.close()
                return self._json(400, {"error": str(exc)})

            appointment_end_at = appointment_at + timedelta(minutes=int(service["duration_minutes"]))
            now = utc_now_iso()
            conn.execute(
                """
                INSERT INTO bookings (
                    patient_name,
                    patient_email,
                    patient_phone,
                    reason,
                    service_id,
                    location_id,
                    appointment_at,
                    appointment_end_at,
                    status,
                    source,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 'web', ?)
                """,
                (
                    patient_name,
                    patient_email,
                    patient_phone,
                    reason,
                    int(service_value),
                    int(location_value),
                    appointment_at.isoformat(),
                    appointment_end_at.isoformat(),
                    now,
                ),
            )
            if USE_POSTGRES:
                booking_id = conn.execute(
                    """
                    SELECT id
                    FROM bookings
                    WHERE patient_email = ?
                      AND appointment_at = ?
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (patient_email, appointment_at.isoformat()),
                ).fetchone()["id"]
            else:
                booking_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
            row = conn.execute(
                """
                SELECT b.*, s.name AS service_name, l.name AS location_name
                FROM bookings b
                JOIN services s ON s.id = b.service_id
                JOIN locations l ON l.id = b.location_id
                WHERE b.id = ?
                """,
                (booking_id,),
            ).fetchone()
            booking = serialize_booking(row)
            create_notification(
                conn,
                booking_id,
                "booking_created",
                "New booking received",
                f"{booking['patientName']} booked {booking['serviceName']} at {booking['locationName']}.",
            )
            email_sent, email_error = send_booking_email(booking)
            if email_sent:
                create_notification(
                    conn,
                    booking_id,
                    "email_sent",
                    "Email notification sent",
                    f"Booking email delivered for {booking['patientName']}.",
                )
            elif email_error:
                create_notification(
                    conn,
                    booking_id,
                    "email_pending",
                    "Email not configured",
                    f"In-app notification saved. Email delivery is inactive: {email_error}",
                )
            conn.commit()
            conn.close()
            return self._json(
                201,
                {
                    "booking": booking,
                    "message": "Appointment request sent successfully. The doctor can now review it in the dashboard.",
                },
            )

        if path == "/api/doctor/login":
            email = normalize_text(data.get("email")).lower()
            password = normalize_text(data.get("password"))
            if not email or not password:
                return self._json(400, {"error": "email and password are required."})
            conn = db_conn()
            doctor = conn.execute("SELECT * FROM doctor_accounts WHERE lower(email) = ?", (email,)).fetchone()
            conn.close()
            if not doctor or not verify_password(password, doctor["password_salt"], doctor["password_hash"]):
                return self._json(401, {"error": "Invalid doctor credentials."})
            token = uuid.uuid4().hex
            payload = {"id": doctor["id"], "name": doctor["name"], "email": doctor["email"]}
            SESSIONS[token] = payload
            return self._json(
                200,
                {"doctor": payload},
                headers={
                    "Set-Cookie": f"{SESSION_COOKIE}={token}; HttpOnly; Path=/; SameSite=Lax"
                },
            )

        if path == "/api/doctor/logout":
            token = self._session_token()
            if token:
                SESSIONS.pop(token, None)
            return self._json(
                200,
                {"ok": True},
                headers={
                    "Set-Cookie": f"{SESSION_COOKIE}=; HttpOnly; Path=/; Max-Age=0; SameSite=Lax"
                },
            )

        if path == "/api/doctor/locks":
            doctor = self._require_auth()
            if not doctor:
                return
            try:
                start_at = parse_iso_datetime(data.get("startAt"))
                end_at = parse_iso_datetime(data.get("endAt"))
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            note = normalize_text(data.get("note")) or "Doctor unavailable"
            location_value = normalize_text(str(data.get("locationId", "")))
            location_id = int(location_value) if location_value.isdigit() else None
            if end_at <= start_at:
                return self._json(400, {"error": "Lock end time must be after the start time."})
            conn = db_conn()
            if location_id is not None and not location_exists(conn, location_id):
                conn.close()
                return self._json(400, {"error": "Selected location was not found."})
            conn.execute(
                """
                INSERT INTO schedule_locks (location_id, start_at, end_at, note, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (location_id, start_at.isoformat(), end_at.isoformat(), note, utc_now_iso()),
            )
            conn.commit()
            locks = fetch_locks(conn)
            conn.close()
            return self._json(201, {"locks": locks})

        booking_id = self._booking_id_from_status_path(path)
        if booking_id:
            doctor = self._require_auth()
            if not doctor:
                return
            status = normalize_text(data.get("status")).lower()
            if status not in {"pending", "confirmed", "cancelled"}:
                return self._json(400, {"error": "status must be pending, confirmed, or cancelled."})
            conn = db_conn()
            booking = conn.execute("SELECT id FROM bookings WHERE id = ?", (booking_id,)).fetchone()
            if not booking:
                conn.close()
                return self._json(404, {"error": "Booking not found."})
            conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
            create_notification(
                conn,
                booking_id,
                "booking_status",
                "Booking updated",
                f"Booking #{booking_id} marked as {status}.",
            )
            conn.commit()
            bookings = fetch_bookings(conn)
            notifications = fetch_notifications(conn)
            conn.close()
            return self._json(200, {"bookings": bookings, "notifications": notifications})

        return self._json(404, {"error": "Route not found."})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        lock_id = self._lock_id_from_path(path)
        if not lock_id:
            return self._json(404, {"error": "Route not found."})
        doctor = self._require_auth()
        if not doctor:
            return
        conn = db_conn()
        exists = conn.execute("SELECT id FROM schedule_locks WHERE id = ?", (lock_id,)).fetchone()
        if not exists:
            conn.close()
            return self._json(404, {"error": "Lock not found."})
        conn.execute("DELETE FROM schedule_locks WHERE id = ?", (lock_id,))
        conn.commit()
        locks = fetch_locks(conn)
        conn.close()
        return self._json(200, {"locks": locks})


def main():
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Doctor booking server running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
