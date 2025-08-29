import os, json
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def load_firebase_credentials():
    try:
        return credentials.Certificate("secrets/serviceAccountKey.json")
    except FileNotFoundError:
        try:
            raw = st.secrets["FIREBASE_KEY_JSON"]
            return credentials.Certificate(dict(raw))
        except Exception as e:
            raise ValueError("Firebase credentials not found.")

def initialize_firebase():
    if not firebase_admin._apps:
        cred = load_firebase_credentials()
        firebase_admin.initialize_app(cred)
    return firestore.client()