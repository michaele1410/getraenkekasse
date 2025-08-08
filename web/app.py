import os
import psycopg2
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# DB-Konfiguration über Umgebungsvariablen
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "getraenkekasse")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "johndoe")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kasse (
                    id SERIAL PRIMARY KEY,
                    datum DATE NOT NULL,
                    vollgut INTEGER,
                    leergut INTEGER,
                    inventar INTEGER,
                    einnahme NUMERIC(10,2),
                    ausgabe NUMERIC(10,2),
                    kassenbestand NUMERIC(10,2),
                    bemerkung TEXT
                );
            """)
        conn.commit()

@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM kasse ORDER BY datum, id")
    daten = cur.fetchall()

    # Berechnung von Inventar und Kassenbestand
    berechnete_daten = []
    inventar = 0
    kassenbestand = 0
    for eintrag in daten:
        id, datum, vollgut, leergut, _, einnahme, ausgabe, _, bemerkung = eintrag
        vollgut = vollgut or 0
        leergut = leergut or 0
        einnahme = float(einnahme or 0)
        ausgabe = float(ausgabe or 0)
        inventar += vollgut - leergut
        kassenbestand += einnahme - ausgabe
        berechnete_daten.append((id, datum, vollgut, leergut, inventar, einnahme, ausgabe, kassenbestand, bemerkung))

    cur.close()
    conn.close()

    return render_template("table.html", daten=berechnete_daten,
                           aktuelles_inventar=inventar,
                           aktueller_kassenbestand=kassenbestand)

@app.route("/add", methods=["POST"])
def add():
    datum = request.form["datum"]
    vollgut = int(request.form.get("vollgut") or 0)
    leergut = int(request.form.get("leergut") or 0)
    einnahme = float(request.form.get("einnahme") or 0)
    ausgabe = float(request.form.get("ausgabe") or 0)
    bemerkung = request.form.get("bemerkung", "")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO kasse (datum, vollgut, leergut, inventar, einnahme, ausgabe, kassenbestand, bemerkung)
        VALUES (%s, %s, %s, 0, %s, %s, 0, %s)
    """, (datum, vollgut, leergut, einnahme, ausgabe, bemerkung))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM kasse WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        datum = request.form["datum"]
        vollgut = int(request.form.get("vollgut") or 0)
        leergut = int(request.form.get("leergut") or 0)
        einnahme = float(request.form.get("einnahme") or 0)
        ausgabe = float(request.form.get("ausgabe") or 0)
        bemerkung = request.form.get("bemerkung", "")
        cur.execute("""
            UPDATE kasse
            SET datum=%s, vollgut=%s, leergut=%s, einnahme=%s, ausgabe=%s, bemerkung=%s
            WHERE id=%s
        """, (datum, vollgut, leergut, einnahme, ausgabe, bemerkung, id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/")

    cur.execute("SELECT * FROM kasse WHERE id = %s", (id,))
    eintrag = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("form.html", eintrag=eintrag)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)