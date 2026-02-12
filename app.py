import pandas as pd
import sqlite3
import streamlit as st 

from database import init_database, clear_db, insert_aircraft
from scraper import scrape_page



init_database()
aircrafts = scrape_page() 
insert_aircraft(aircrafts)

