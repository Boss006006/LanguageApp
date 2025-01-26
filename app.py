#region ---- Import modules ----
import pandas as pd
import pyodbc
import streamlit as st
from streamlit_option_menu import option_menu
import time
import os

#endregion

#region ---- Create database connection
server = 'DESKTOP-LM53HA6\\SQLEXPRESS'
database = 'LanguageApp'
username = os.getenv('DB_LOGIN')
password = os.getenv('DB_PASSWORD')

connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
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

with st.sidebar:
    general_menu = option_menu(
            menu_title='Menu'
        ,   options = ['Words', 'Input Words', 'Grammar']
        ,   orientation = 'Vertical'   

    )

#endregion

#region ---- Practice words ----
if general_menu == 'Words':
    st.title('Practice words')

    with pyodbc.connect(connection_string) as conn:
        print("Connection successful!")

        # Fetch data into a DataFrame
        query = "SELECT * FROM L_Translations"
        df_words = pd.read_sql(query, conn)


    st.write('---')

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

#endregion

#region ---- Input Words ----
if general_menu == 'Input Words':
    st.title('Input words')

    # Input fields for Dutch, English, and Spanish
    dutch_word = st.text_input("Dutch Word", placeholder="Enter the Dutch word")
    english_word = st.text_input("English Word", placeholder="Enter the English word")
    spanish_word = st.text_input("Spanish Word", placeholder="Enter the Spanish word")

    # Submit button
    if st.button("Submit"):
        # Check if all fields are filled
        if dutch_word and english_word and spanish_word:
            try:
                # Connect to the database and insert the new row
                with pyodbc.connect(connection_string) as conn:
                    cursor = conn.cursor()
                    insert_query = """
                    INSERT INTO L_Translations (Dutch, English, Spanish)
                    VALUES (?, ?, ?)
                    """
                    cursor.execute(insert_query, (dutch_word, english_word, spanish_word))
                    conn.commit()
                    st.success("New words inserted successfully!")
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.warning("Please fill in all fields before submitting.")
#endregion



