import sqlite3

def init_database():
    conn = sqlite3.connect("aircraft.db")
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    eur_price REAL,
    foreign_price REAL,
    currency TEXT          
    )
    """)

    conn.commit()
    conn.close()


def clear_db():
    conn = sqlite3.connect("aircraft.db")
    cur = conn.cursor()
    
    cur.execute("DELETE FROM aircraft")

    conn.commit()
    conn.close()

def insert_aircraft(aircrafts):
    conn = sqlite3.connect("aircraft.db")
    cur = conn.cursor()

    cur.executemany("""
    INSERT INTO aircraft (url, brand, model, eur_price, foreign_price, currency)
    VALUES (?, ?, ?, ?, ?, ?)
    """, [(a["url"], a["brand"], a["model"], a["eur_price"], a["foreign_price"], a["currency"])
          for a in aircrafts])
       
    conn.commit()
    conn.close()