#region ---- Import modules ----
import pandas as pd
import pyodbc
import streamlit as st
from streamlit_option_menu import option_menu
import time
import os
import mysql.connector
from mysql.connector import Error
import openpyxl

#endregion

#endregion
 
#region ---- Home Page and Configuration ----
st.set_page_config(
        page_title = 'LanguageApp'
    ,   layout = 'wide'
)

col1, col2 = st.columns([3,1])

col1.title('Mergengues and Schuimgebakjes')

col2.image("image.png"
    ,   use_container_width=True)

st.write("---")

with st.sidebar:
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()

with st.sidebar:
    general_menu = option_menu(
            menu_title='Menu'
        ,   options = ['Words', 'Input Words', 'Grammar', 'ES Verbs', 'NL Verbs']
        ,   orientation = 'Vertical'   

    )

#endregion

#region ---- Authentication ----

#endregion

#region ---- Create database connection ----

DB_LOGIN = os.getenv("DB_LOGIN")
DB_PASSWORD = os.getenv("DB_PASSWORD")

#DB_LOGIN = st.secrets["DB_LOGIN"]
#DB_PASSWORD = st.secrets["DB_PASSWORD"]

db_config = {
    'host': 'sql7.freesqldatabase.com',
    'database': DB_LOGIN,
    'user': DB_LOGIN,
    'password': DB_PASSWORD,
    'port': 3306
}

connection = mysql.connector.connect(**db_config)

connection.is_connected()
print("Connected to the database successfully!")
cursor = connection.cursor()
cursor.execute("SHOW TABLES;")
tables = cursor.fetchall()
print("Tables:", tables)

#TODO: Fix cachin error
#@st.cache_resource
def get_connection():
    """Establish and cache the database connection."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        st.error(f"Error: {e}")
        st.error("Refresh the page")
        return None

@st.cache_data
def load_data(table_name):
    """Load _L_L_WORDS table into a Pandas DataFrame."""
    conn = get_connection()
    if conn:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    else:
        return pd.DataFrame() 

#endregion
    
#region ---- Practice words ----

df_words = load_data(table_name='_L_L_WORDS')

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

#endregion

#region ---- Spanish Verbs ----

# Create series with indices to slice the dataset on
df_verbsES = pd.read_excel("Verbs.xlsx", sheet_name= 'Spanish', header=None)

end_value = len(df_verbsES)
series = {}
current_series = 1
series[f'serie{current_series}'] = []
counter = 0

for number in range(end_value + 1):
    if counter % 7 == 6:  
        counter += 1  
        continue  
    if len(series[f'serie{current_series}']) == 6: 
        current_series += 1
        series[f'serie{current_series}'] = []
    series[f'serie{current_series}'].append(number)
    counter += 1

# Create a separate dataframe for each verb
df_length = len(df_verbsES)

verbs = []

# Loop through each series in the dictionary
for key, indices in series.items():
    # Ensure all indices are within the bounds of the DataFrame
    valid_indices = [index for index in indices if index < df_length]
    # Create a new dataframe for each series using only valid indices
    if valid_indices:  # Only if there are valid indices
        # Temporarily create the dataframe to extract the name and set the column names
        temp_df = df_verbsES.iloc[valid_indices]
        # Get the name from the first row, first column
        df_name = temp_df.iloc[0, 0]
        verbs.append(df_name)
        temp_df = temp_df.reset_index(drop=True)

        # Use the first row as the header and the rest as the data
        temp_df.columns = temp_df.iloc[0]  # Set the first row as the header
        temp_df = temp_df[1:]  # Drop the first row to remove it as data

        globals()[df_name] = temp_df.reset_index(drop=True)
        #globals()[df_name].iloc[0, 0] = ''

if general_menu == "ES Verbs":

    # Define times and language
    languages = ["Espanol", "English"]
    times = ["Present", "Preterite", "Imperfect", "Future", "Conditional"]
    
    st.header("Verbs to learn")

    # Create selection menus

    col1, col2, col3 = st.columns(3)

    selected_verbs = col1.multiselect("Select verb", verbs)
    selected_language = col2.multiselect("Select language", languages, default=languages) 
    selected_times = col3.multiselect("Select time", times, default=times)

    first_column_name = 'Infinitive'  

    selected_columns = [f"{time}_{lang[:2].upper()}" for lang in selected_language for time in selected_times]

    # Display
    for verb_name in selected_verbs:
        st.write(f"The name of the verb is {verb_name}")

        # Get all columns from the dataframe
        all_columns = list(globals()[verb_name].columns)

        # The first column name is the same as the verb_name
        first_column_name = verb_name  
        
        # Build the selected columns based on the selected language and time
        # We first include the first column name to ensure it's always present
        time_language_columns = [
            f"{time}_{lang[:2].upper()}" for lang in selected_language for time in selected_times
        ]

        # Insert the first column at the beginning if it's not already included
        if first_column_name not in time_language_columns:
            time_language_columns.insert(0, first_column_name)

        # Filter the all_columns to only include the ones in selected_columns, preserving the original order
        selected_columns_ordered = [col for col in all_columns if col in time_language_columns]

        # Display the dataframe with the ordered selected columns
        st.dataframe(globals()[verb_name][selected_columns_ordered])

# endregion

#region ---- NL Verbs ----

# Create series with indices to slice the dataset on
df_verbsNL = pd.read_excel("Verbs.xlsx", sheet_name= 'Dutch', header=None)

end_value = len(df_verbsNL)
series = {}
current_series = 1
series[f'serie{current_series}'] = []
counter = 0

for number in range(end_value + 1):
    if counter % 7 == 6:  
        counter += 1  
        continue  
    if len(series[f'serie{current_series}']) == 6: 
        current_series += 1
        series[f'serie{current_series}'] = []
    series[f'serie{current_series}'].append(number)
    counter += 1

# Create a separate dataframe for each verb
df_length = len(df_verbsNL)

verbs = []

# Loop through each series in the dictionary
for key, indices in series.items():
    # Ensure all indices are within the bounds of the DataFrame
    valid_indices = [index for index in indices if index < df_length]
    # Create a new dataframe for each series using only valid indices
    if valid_indices:  # Only if there are valid indices
        # Temporarily create the dataframe to extract the name and set the column names
        temp_df = df_verbsNL.iloc[valid_indices]
        # Get the name from the first row, first column
        df_name = temp_df.iloc[0, 0]
        verbs.append(df_name)
        temp_df = temp_df.reset_index(drop=True)

        # Use the first row as the header and the rest as the data
        temp_df.columns = temp_df.iloc[0]  # Set the first row as the header
        temp_df = temp_df[1:]  # Drop the first row to remove it as data

        globals()[df_name] = temp_df.reset_index(drop=True)
        #globals()[df_name].iloc[0, 0] = ''

if general_menu == "NL Verbs":

    # Define times and language
    languages = ["Dutch", "English"]
    times = ["TT", "OVT", "VTT", "VVT"]
    
    st.header("Verbs to learn")

    st.info("""
    TT = Tegenwoordige Tijd (Present)   
    OVT = Onvoltooid Verleden Tijd (Simple Past Tense)  
    VTT = Voltooid Tegenwoordige Tijd (Present Perfect Tense)  
    VVT = Voltooid Verleden Tijd (Past Perfect Tense/Conditional)  
    """)

    # Create selection menus
    col1, col2, col3 = st.columns(3)

    selected_verbs = col1.multiselect("Select verb", verbs)
    selected_language = col2.multiselect("Select language", languages, default=languages) 
    selected_times = col3.multiselect("Select time", times, default=times)

    first_column_name = 'Infinitive'  

    selected_columns = [f"{time}_{lang[:2].upper()}" for lang in selected_language for time in selected_times]

    # Display
    for verb_name in selected_verbs:
        st.write(f"The name of the verb is {verb_name}")

        # Get all columns from the dataframe
        all_columns = list(globals()[verb_name].columns)

        # The first column name is the same as the verb_name
        first_column_name = verb_name  
        
        # Build the selected columns based on the selected language and time
        # We first include the first column name to ensure it's always present
        time_language_columns = [
            f"{time}_{lang[:2].upper()}" for lang in selected_language for time in selected_times
        ]

        # Insert the first column at the beginning if it's not already included
        if first_column_name not in time_language_columns:
            time_language_columns.insert(0, first_column_name)

        # Filter the all_columns to only include the ones in selected_columns, preserving the original order
        selected_columns_ordered = [col for col in all_columns if col in time_language_columns]

        # Display the dataframe with the ordered selected columns
        st.dataframe(globals()[verb_name][selected_columns_ordered])

#endregion