import streamlit as st
import pymongo
import pandas as pd

# Establish the MongoDB connection
def get_database():
    uri = st.secrets["mongo"]["uri"]  # Read from environment variable
    if not uri:
        raise ValueError("Please set the MONGODB_URI environment variable!")
    client = pymongo.MongoClient(uri)
    return client.fickse_probablyat

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

def get_rating_for_user_and_event(current_user, event):
    db = get_database()
    document = db.Bewertungen.find_one({current_user: {"$exists": True}})
    
    value = document.get(current_user) if document else None
    ratings = None

    if value:
        ratings_dict = value.get(event)
        if ratings_dict:
            ratings = pd.DataFrame(list(ratings_dict.items()), columns=["Mitglied", "Bewertung"])

    if ratings is None:
        st.warning(f"Du hast noche keine Bewertung für {event}!")
        users = get_users()
        users.remove(current_user)
        ratings = pd.DataFrame({"Mitglied": users,"Bewertung": [3 for _ in users]})

    return ratings

def update_rating(current_user, update_data):
    db = get_database()
    db.Bewertungen.update_one({current_user: {"$exists": True}}, update_data, upsert=True)

current_user = st.selectbox("Du bist", get_users())
event = st.selectbox("Veranstaltung", get_events())
ratings = get_rating_for_user_and_event(current_user, event)

edited_df = st.data_editor(
    ratings,
    column_config={
        "Bewertung": st.column_config.NumberColumn(
            "Deine Bewertung",
            help="Wie fandest du die Performance (1-5)?",
            min_value=1,
            max_value=5,
            step=1,
            format="%d ⭐",
        ),
    },
    hide_index=True,
    use_container_width=True,
    disabled="Mitglied",
)

edited_df["Mitglied"] = f"{current_user}.{event}." + edited_df["Mitglied"].astype('str')
new_ratings = dict(zip(edited_df['Mitglied'], edited_df['Bewertung']))
update_rating(current_user, {"$set": new_ratings})
