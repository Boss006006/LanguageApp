#region ---- Import modules ----
import pandas as pd
import pyodbc
import streamlit as st
from streamlit_option_menu import option_menu
import time
import os
import mysql.connector
from mysql.connector import Error

#endregion

#region ---- Create database connection

#DB_LOGIN = os.getenv("DB_LOGIN")
#DB_PASSWORD = os.getenv("DB_PASSWORD")

# Debugging line (remove after checking)
st.write("Secrets available:", st.secrets)

# Use `.get()` to prevent errors if secrets are missing
DB_LOGIN = st.secrets["DB_LOGIN"]
DB_PASSWORD = st.secrets.get["DB_PASSWORD"]

st.write('TEMP')
st.write(DB_LOGIN)
st.write(DB_PASSWORD)

if not DB_LOGIN or not DB_PASSWORD:
    st.error("Database credentials are missing! Set them in Streamlit Cloud.")

db_config = {
    'host': 'sql7.freesqldatabase.com',
    'database': 'sql7760550',
    'user': 'sql7760550',
    'password': 'IZvd79hE57',
    'port': 3306
}

try:
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        print("Connected to the database successfully!")
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("Tables:", tables)

except Error as e:
    print(f"Error: {e}")

#endregion
 
#region ---- Page Configuration ----
st.set_page_config(
        page_title = 'LanguageApp'
    ,   layout = 'wide'
)

#endregion

#region ---- Authentication ----

#endregion

#region ---- Homepage ----
st.title('Mergengues and Schuimgebakjes')
st.write("---")

if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()

with st.sidebar:
    general_menu = option_menu(
            menu_title='Menu'
        ,   options = ['Words', 'Input Words', 'Grammar']
        ,   orientation = 'Vertical'   

    )

#endregion

### DEV

#TODO: Fix cachin error
#@st.cache_resource
def get_connection():
    """Establish and cache the database connection."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        st.error(f"Error: {e}")
        return None

@st.cache_data
def load_data():
    """Load _L_L_WORDS table into a Pandas DataFrame."""
    conn = get_connection()
    if conn:
        query = "SELECT * FROM _L_L_WORDS;"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    else:
        return pd.DataFrame() 
    
#region ---- Practice words ----

#TODO: Add parameter to use function for new tables
df_words = load_data()

if general_menu == 'Words':
    st.title('Practice words')

    # Display headers just once
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.subheader("🇳🇱 Dutch")
    with col2:
        st.subheader("🇬🇧 English")
    with col3:
        st.subheader("🇪🇸 Spanish")

    # Display the words row by row
    for index, row in df_words.iterrows():
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.write(f"<h5 style='color: #333;'>{row['Dutch']}</h5>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<h5 style='color: #333;'>{row['English']}</h5>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<h5 style='color: #333;'>{row['Spanish']}</h5>", unsafe_allow_html=True)


### DEV

