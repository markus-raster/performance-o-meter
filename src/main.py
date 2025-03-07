import streamlit as st
import pymongo
import pandas as pd
st. set_page_config(layout="wide")

# Establish the MongoDB connection
def get_database():
    uri = st.secrets["mongo"]["uri"]  # Read from environment variable
    if not uri:
        raise ValueError("Please set the MONGODB_URI environment variable!")
    client = pymongo.MongoClient(uri)
    return client.fickse_toywestern

# Pull users from the collection
@st.cache_data(ttl=600, show_spinner=False)
def get_users():
    db = get_database()
    items = db.Mitglieder.find({}, {"name": 1})
    return sorted(doc["name"] for doc in items)

@st.cache_data(ttl=600, show_spinner=False)
def get_events():
    db = get_database()
    items = db.Veranstaltungen.find({}, {"name": 1})
    return [doc["name"] for doc in items]

@st.cache_data(None, show_spinner=False, max_entries=1)
def get_rating_for_user_and_event(current_user, event):
    db = get_database()
    document = db.Bewertungen.find_one({current_user: {"$exists": True}})
    
    value = document.get(current_user) if document else None
    ratings = None

    if value:
        ratings_dict = value.get(event)
        if ratings_dict:
            # Creating a DataFrame from the dictionary
            ratings = pd.DataFrame.from_dict(ratings_dict, orient='index', columns=['Bewertung', 'Begründung'])
            ratings.reset_index(inplace=True)
            ratings.rename(columns={'index': 'Mitglied'}, inplace=True)


    if ratings is None:
        st.warning(f"Du hast noche keine Bewertung für {event}!")
        users = get_users()
        users.remove(current_user)
        ratings = pd.DataFrame({"Mitglied": users,"Bewertung": [None for _ in users], "Begründung" : [None for _ in users]})

    return ratings

def update_rating(current_user, update_data):
    db = get_database()
    db.Bewertungen.update_one({current_user: {"$exists": True}}, update_data, upsert=True)

st.markdown("<h1 style='text-align: center; color: #ff3377;'>Fickse Performance Rating</h1>", unsafe_allow_html=True)


user = st.empty()
password = st.empty()

current_user = user.selectbox("Du bist", get_users())
pw = password.text_input("Passwort", type="password")

if pw == current_user[0:2] + "nomt":
    user.empty()
    password.empty()
    event = st.selectbox("Veranstaltung", get_events())
    ratings = get_rating_for_user_and_event(current_user, event)

    # hier könnten wir eigtl cachen bis wir den user oder die veranstaltung wechseln
    edited_df = st.data_editor(
        ratings,
        column_config={
            "Bewertung": st.column_config.SelectboxColumn(
                "Deine Bewertung",
                help="Wie fandest du die Performance (1-5)?",
                options=[1, 2, 3, 4, 5],
                required=False,
            ),
            "Begründung": st.column_config.TextColumn(
                "Deine Begründung für die Performance des Aktuers",
                help="Schreibe einen kreativen Text warum der Fickse Aktuer deine Bewerung bekommen hat.",
                required=False

            )
        },
        hide_index=True,
        use_container_width=True,
        disabled=["Mitglied"],
        key="data"
        
    )

    edited_df["Mitglied"] = f"{current_user}.{event}." + edited_df["Mitglied"].astype('str')
    new_ratings = dict(zip(edited_df['Mitglied'], zip(edited_df['Bewertung'], edited_df['Begründung'])))
    update_rating(current_user, {"$set": new_ratings})

else:
    if pw != "":
        st.warning("Bitte das korrekte Passwort eingeben.")