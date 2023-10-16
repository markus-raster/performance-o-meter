import streamlit as st
import pymongo
import pandas as pd

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient("mongodb://fickse_probablyat:35b6e41ff5b02cab42905b5de5e16e935d1a6e8f@161.97.121.243:27018/fickse_probablyat")

client = init_connection()

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_users():
    db = client.fickse_probablyat
    items = db.Mitglieder.find()
    items = list(items)  # make hashable for st.cache_data
    users = [doc["name"] for doc in items]
    return users

@st.cache_data(ttl=0)
def get_events():
    db = client.fickse_probablyat
    items = db.Veranstaltungen.find()
    items = list(items)  # make hashable for st.cache_data
    names = [doc["name"] for doc in items]
    return names

def get_rating_for_user_and_event(current_user, event):
    db = client.fickse_probablyat
    collection = db.Bewertungen
    # Fetch the document containing the "Markus" key
    document = collection.find_one({current_user: {"$exists": True}})
    # Extract the value associated with "Markus" or set to None if not present
    value = document.get("Markus") if document else None

    if value is not None:
        ratings = value.get(event)
    else:
        ratings = None

    if ratings is None:
        st.warning(f"Du hast noche keine Bewertung für {event}!")
        users = get_users()
        users.remove(current_user)
        ratings = pd.DataFrame({"Mitglied": users,"Bewertung": [3 for _ in range(len(users))]})

    return ratings

current_user = "Markus Raster"
event = "Niederbühl"

events = get_events()
event = st.selectbox("Veranstaltung", events)
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
)

st.write(edited_df.to_dict())