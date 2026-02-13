import pandas as pd
import sqlite3
import streamlit as st 

from database import init_database, insert_aircraft
from scraper import scrape_page



init_database()
aircrafts, run_time = scrape_page() 
insert_aircraft(aircrafts, run_time)

