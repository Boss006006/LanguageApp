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
from datetime import datetime

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
        ,   options = ['Words', 'Add Words', 'Practice Words', 'Grammar', 'ES Verbs', 'NL Verbs']
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

#endregion

#region ---- Load and Cache data ----

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

#@st.cache_data
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

#@st.cache_resource
def insert_words(dutch, english, spanish):
    """Insert new words into the database."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = "INSERT INTO _L_L_WORDS (Dutch, English, Spanish) VALUES (%s, %s, %s)"
            cursor.execute(query, (dutch, english, spanish))
            conn.commit()  # Commit to save changes
            st.success(f"Word {english} saved successfully.")

        except Error as e:
            st.error(f"Error: {e}")
            conn.rollback()  # Rollback in case of error
        finally:
            conn.close()
    else:
        st.error("Failed to connect to the database.") 

def update_score(english, score, column_name):
    """Update the Score for a word in the _L_L_WORDS table."""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = f"UPDATE _L_L_WORDS SET {column_name} = %s WHERE English = %s"
            cursor.execute(query, (score, english))
            conn.commit()  # Commit to save changes

        except Error as e:
            st.error(f"Error updating score for {english}: {e}")
            conn.rollback()  # Rollback in case of error
        finally:
            conn.close()
    else:
        st.error("Failed to connect to the database for updating scores.")


df_words = load_data(table_name='_L_L_WORDS')
df_words['Date'] = pd.to_datetime(df_words['DTS']).dt.date  # Convert to date format

#endregion

#region ---- Add Words ----

if general_menu == "Add Words":

    st.header("Words to learn")

    st.write("Write down the Dutch, English and Spanish words to add them to the database with words to learn. "\
         "Please write down all words without capitals, except when the word must always be written with a capital" 
         )
     
    with st.form("Noun_sustantivo", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        dutch_word = col1.text_input("Enter Dutch word")
        english_word = col2.text_input("Enter English word")
        spanish_word = col3.text_input("Enter Spanish word")

        submitted = st.form_submit_button("Save words")
        
        if submitted and not any(df_words["English"].str.lower() == english_word.lower()):
            insert_words(dutch_word, english_word, spanish_word)
        else:
            if english_word.lower() in df_words["English"].str.lower().values:
                st.warning(f"The word {english_word} already exists")

#endregion

#region ---- Words ----

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

#region ---- Practice Words ----

if general_menu == 'Practice Words':

    language_menu = option_menu(options = ['Spanish', 'Dutch'], menu_title=None, orientation='horizontal')
    practice_words_df = df_words.sample(0)

    if language_menu == 'Spanish':
        st.subheader('Lets practice Spanish')

        st.info("""Pick a number of words you want to practice. Each time you have the correct answer, the score
            goes up by 1. Lower the score to only pick words with a lower score. Select a start and end date to choose
            a period when the words were added to the data. The minimum date is 31-01-2025, when the first word was added.""")

        num_input, cutoff_input, cut_off_date1, cut_off_date2, num_button = st.columns([1.5,1.5,1.5,1.5,2])

        min_score = min(df_words["Score_ES"])
        max_score = max(df_words["Score_ES"])

        N_practice_words = num_input.number_input("Number of words:", min_value=0, 
            max_value=len(df_words), step=1, value=0)
        cutoff_value = cutoff_input.number_input("Enter score cutoff:", 
            min_value=min_score, max_value=max_score, value=max_score)
        
        # Define the minimum date
        min_date_value = datetime(2025, 1, 31).date()

        # Add date picker widget with a minimum date and default value

        min_date = cut_off_date1.date_input("Select a start date:", 
                                        min_value=min_date_value,
                                        max_value=pd.Timestamp('today').date(),
                                        value=min_date_value
                                        )
        end_date = cut_off_date2.date_input("Select an end date:", 
                                        min_value=min_date_value,
                                        max_value=pd.Timestamp('today').date(),
                                        value=pd.Timestamp('today').date()
                                        )

        num_button.markdown(" ")
        num_button.markdown(" ")

        if num_button.button("Click to start practice:"):
            filtered_words_df = df_words[(df_words["Score_ES"] <= cutoff_value) 
                                        & (df_words["Date"] <= end_date)
                                        & (df_words["Date"] >= min_date)]

            if not filtered_words_df.empty:
                if N_practice_words > len(filtered_words_df):
                    st.write("The number of words requested exceeds the available words. Adjusting to maximum available.")
                    N_practice_words = len(filtered_words_df)  

                if N_practice_words > 0:
                    practice_words_df = filtered_words_df.sample(N_practice_words)
                else:
                    st.write("Select at least 1 word")
                    practice_words_df = df_words.sample(N_practice_words)
            else:
                st.write("No words found for the selected criteria. Please adjust your selection.")
                N_practice_words = 0
                
        words_column, practice_words_column = st.columns(2)
        
    # Practice the words
        if 'answers' not in st.session_state:
            st.session_state.answers = ["" for _ in range(len(practice_words_df))]

        with st.form(key='practice_form'):
            # TODO: Write the new values to the state_session answers instead of using the keys 
            for index, question in enumerate(practice_words_df["English"]):
                spacer2, words_question, word_answer = st.columns([2,1,3])

                words_question.markdown(" ")
                words_question.markdown(" ")

                words_question.markdown(f"Translate: **{question}**")
                current_answer = word_answer.text_input(f"Translate word {index + 1}:",  key=f"{index}_{question}")

            if N_practice_words > 0:
                spacer2, words_question, word_answer = st.columns([2,1,3])
                submit_button = word_answer.form_submit_button(label='Submit answers')

                if submit_button:
                    st.markdown("## Your Answers: ")

                    dict_words_temp = dict(st.session_state)
                    filtered_dict_words_temp = {key.split('_')[-1]: value for key, value in dict_words_temp.items() if '_' in key}
                    
                    wrong_answers = 0

                    for key, value in filtered_dict_words_temp.items():
                        
                        if key in df_words["English"].values:
                            correct_answer_row = df_words[df_words['English'] == key]
                            if not correct_answer_row.empty:
                                correct_answer = correct_answer_row['Spanish'].iloc[0]
                            else:
                                correct_answer = None

                            if value == correct_answer:
                                st.markdown(f"<span style='color: green;'>English word: <b>{key}</b> || Your answer: <b>{value}</b> is correct</span>", unsafe_allow_html=True)
                            if value != correct_answer:
                                st.markdown(f"<span style='color: darkred;'>English word: <b>{key}</b> || Your answer: <b>{value}</b> || Correct answer: <b>{correct_answer}</b></span>", unsafe_allow_html=True)
                                wrong_answers += 1

                    if wrong_answers == 0:
                        st.write("All answers correct!")
                        st.balloons()
        
                if submit_button:

                    dict_words = dict(st.session_state)
                    filtered_dict_words = {key.split('_')[-1]: value for key, value in dict_words.items() if '_' in key}
                
                    changed_score_keys = []

                    for key, value in filtered_dict_words.items():
                        mask = (df_words["English"] == key) & (df_words["Spanish"] == value)
                        df_words.loc[mask, "Score_ES"] += 1
                        changed_score_keys.append(key)

                    filtered_df = df_words[df_words['English'].isin(changed_score_keys)]

                    # Assuming filtered_df is your DataFrame with updated scores
                    for index, row in filtered_df.iterrows():
                        update_score(row['English'], row['Score_ES'], 'Score_ES')

    if language_menu == 'Dutch':
            st.subheader('Letc practice Dutch')

            st.info("""Pick a number of words you want to practice. Each time you have the correct answer, the score
                    goes up by 1. Lower the score to only pick words with a lower score. Select a start and end date to choose
                    a period when the words were added to the data. The minimum date is 31-01-2025, when the first word was added.""")

            num_input, cutoff_input, cut_off_date1, cut_off_date2, num_button = st.columns([1.5,1.5,1.5,1.5,2])

            min_score = min(df_words["Score_NL"])
            max_score = max(df_words["Score_NL"])

            N_practice_words = num_input.number_input("Number of words:", min_value=0, 
                max_value=len(df_words), step=1, value=0)
            cutoff_value = cutoff_input.number_input("Enter score cutoff:", 
                min_value=min_score, max_value=max_score, value=max_score)
            
            # Define the minimum date
            min_date_value = datetime(2025, 1, 31).date()

            # Add date picker widget with a minimum date and default value

            min_date = cut_off_date1.date_input("Select a start date:", 
                                            min_value=min_date_value,
                                            max_value=pd.Timestamp('today').date(),
                                            value=min_date_value
                                            )
            end_date = cut_off_date2.date_input("Select an end date:", 
                                            min_value=min_date_value,
                                            max_value=pd.Timestamp('today').date(),
                                            value=pd.Timestamp('today').date()
                                            )

            num_button.markdown(" ")
            num_button.markdown(" ")

            if num_button.button("Click to start practice:"):
                filtered_words_df = df_words[(df_words["Score_NL"] <= cutoff_value) 
                                            & (df_words["Date"] <= end_date)
                                            & (df_words["Date"] >= min_date)]

                if not filtered_words_df.empty:
                    if N_practice_words > len(filtered_words_df):
                        st.write("The number of words requested exceeds the available words. Adjusting to maximum available.")
                        N_practice_words = len(filtered_words_df)  

                    if N_practice_words > 0:
                        practice_words_df = filtered_words_df.sample(N_practice_words)
                    else:
                        st.write("Select at least 1 word")
                        practice_words_df = df_words.sample(N_practice_words)
                else:
                    st.write("No words found for the selected criteria. Please adjust your selection.")
                    N_practice_words = 0
                    
            words_column, practice_words_column = st.columns(2)
            
        # Practice the words
            if 'answers' not in st.session_state:
                st.session_state.answers = ["" for _ in range(len(practice_words_df))]

            with st.form(key='practice_form'):
                # TODO: Write the new values to the state_session answers instead of using the keys 
                for index, question in enumerate(practice_words_df["English"]):
                    spacer2, words_question, word_answer = st.columns([2,1,3])

                    words_question.markdown(" ")
                    words_question.markdown(" ")

                    words_question.markdown(f"Translate: **{question}**")
                    current_answer = word_answer.text_input(f"Translate word {index + 1}:",  key=f"{index}_{question}")

                if N_practice_words > 0:
                    spacer2, words_question, word_answer = st.columns([2,1,3])
                    submit_button = word_answer.form_submit_button(label='Submit answers')

                    if submit_button:
                        st.markdown("## Your Answers: ")

                        dict_words_temp = dict(st.session_state)
                        filtered_dict_words_temp = {key.split('_')[-1]: value for key, value in dict_words_temp.items() if '_' in key}
                        
                        wrong_answers = 0

                        for key, value in filtered_dict_words_temp.items():
                            
                            if key in df_words["English"].values:
                                correct_answer_row = df_words[df_words['English'] == key]
                                if not correct_answer_row.empty:
                                    correct_answer = correct_answer_row['Dutch'].iloc[0]
                                else:
                                    correct_answer = None

                                if value == correct_answer:
                                    st.markdown(f"<span style='color: green;'>English word: <b>{key}</b> || Your answer: <b>{value}</b> is correct</span>", unsafe_allow_html=True)
                                if value != correct_answer:
                                    st.markdown(f"<span style='color: darkred;'>English word: <b>{key}</b> || Your answer: <b>{value}</b> || Correct answer: <b>{correct_answer}</b></span>", unsafe_allow_html=True)
                                    wrong_answers += 1

                        if wrong_answers == 0:
                            st.write("All answers correct!")
                            st.balloons()
            
                    if submit_button:

                        dict_words = dict(st.session_state)
                        filtered_dict_words = {key.split('_')[-1]: value for key, value in dict_words.items() if '_' in key}
                    
                        changed_score_keys = []

                        for key, value in filtered_dict_words.items():
                            mask = (df_words["English"] == key) & (df_words["Dutch"] == value)
                            df_words.loc[mask, "Score_NL"] += 1
                            changed_score_keys.append(key)

                        filtered_df = df_words[df_words['English'].isin(changed_score_keys)]

                        # Assuming filtered_df is your DataFrame with updated scores
                        for index, row in filtered_df.iterrows():
                            update_score(row['English'], row['Score_NL'], 'Score_NL')

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