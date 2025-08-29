import os, json
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def load_firebase_credentials():
    try:
        return credentials.Certificate("secrets/serviceAccountKey.json")
    except FileNotFoundError:
        try:
            cred_dict = dict(st.secrets["FIREBASE_KEY_JSON"])  # Explicit conversion
            return credentials.Certificate(cred_dict)
        except KeyError:
            raise ValueError("FIREBASE_KEY_JSON not found in Streamlit secrets.")
        except Exception as e:
            raise ValueError(f"Failed to load Firebase credentials: {e}")

def initialize_firebase():
    if not firebase_admin._apps:
        cred = load_firebase_credentials()
        firebase_admin.initialize_app(cred)
    return firestore.client()