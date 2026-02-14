import sqlite3

def db_conn():
    return sqlite3.connect("aircraft.db")

def init_database():
    with db_conn() as conn:
        cur = conn.cursor()
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS aircraft (
        aircraft_id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        eur_price REAL,
        foreign_price REAL,
        currency TEXT,
        timestamp TEXT NOT NULL,
        active INTEGER NOT NULL         
        )
        """)

        conn.commit()

def insert_aircraft(aircrafts, run_time):

    if not aircrafts:
        return
    
    with db_conn() as conn:
        cur = conn.cursor()

        cur.executemany("""
        INSERT INTO aircraft (url, brand, model, eur_price, foreign_price, currency, timestamp, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
                brand=excluded.brand,
                model=excluded.model,
                eur_price=excluded.eur_price,
                foreign_price=excluded.foreign_price,
                currency=excluded.currency,
                timestamp=excluded.timestamp,
                active=1    
        """, [
            (a["url"], a["brand"], a["model"], a["eur_price"], a["foreign_price"], a["currency"], run_time, a["active"])
            for a in aircrafts
        ])
        
        cur.execute("""
        UPDATE aircraft
        SET active = 0 
        WHERE timestamp != ?
        """, (run_time,))

        conn.commit()