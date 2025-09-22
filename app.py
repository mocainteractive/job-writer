import os
import re
import json
import textwrap
from typing import Optional

import streamlit as st

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(
    page_title="Job Assistant",
    page_icon="https://mocainteractive.com/wp-content/uploads/2025/04/cropped-moca-instagram-icona-1.png",
    layout="wide",
)

# Custom Randstad-like CSS
st.markdown("""
<style>
body {
    background-color: #F7F7F7;
    font-family: "Open Sans", sans-serif;
}

h1, h2, h3, h4 {
    font-weight: 600;
    color: #001C54;
}

/* Pulsante principale */
.stButton button {
    background-color: #0057B8;
    color: white;
    border-radius: 6px;
    padding: 0.6em 1.2em;
    font-size: 1.1em;
    border: none;
    font-weight: 600;
}
.stButton button:hover {
    background-color: #004494;
}

/* Input box */
.stTextInput > div > div > input,
.stTextArea > div > textarea {
    border-radius: 6px;
    border: 1px solid #d9d9d9;
    padding: 0.6em;
    background-color: #ffffff;
}

/* Container padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header con loghi
# -----------------------------
st.markdown("""
<div style="display:flex; align-items:center; justify-content:center; gap:40px; margin-bottom:20px;">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Randstad_Logo.svg/2560px-Randstad_Logo.svg.png" alt="Randstad" style="height:40px;">
  <h1 style="margin:0; font-size:2.2em;">Job Assistant</h1>
  <img src="https://mocainteractive.com/wp-content/uploads/2025/04/cropped-moca_logo-positivo-1.png" alt="Moca" style="height:40px;">
</div>
""", unsafe_allow_html=True)

st.markdown("""
Scrivi una bozza veloce, ci penso io a sistemarla secondo il **tone of voice Randstad**.

**Come funziona:** inserisci *Titolo annuncio* + 4 campi (Descrizione generale, Responsabilità, Qualifiche, Livelli di studio),
poi clicca **Genera annuncio**. L'AI produrrà testo pulito, coerente e professionale.
""")

# -----------------------------
# Secrets & Config
# -----------------------------
DEFAULT_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.warning("⚠️ Imposta la variabile d'ambiente OPENAI_API_KEY o aggiungi st.secrets['OPENAI_API_KEY'].")

# Language fisso
language = "Italiano"

# Tone of voice fisso lato backend
BRAND_VOICE_FALLBACK = """
siamo randstad, il tuo partner nel mondo del lavoro.
... (testo chi siamo Randstad già incluso qui)
""".strip()

brand_text = BRAND_VOICE_FALLBACK

# -----------------------------
# Input form
# -----------------------------
with st.form("job_form", clear_on_submit=False):
    st.subheader("1) Dati annuncio")
    title = st.text_input("Titolo annuncio", placeholder="Es. Addetto/a amministrazione fornitori")

    col1, col2 = st.columns(2)
    with col1:
        descrizione = st.text_area("Descrizione generale (bozza)", height=180, placeholder="Scrivi in libertà: contesto dell'azienda, sede, finalità del ruolo…")
        responsabilita = st.text_area("Responsabilità (bozza)", height=220, placeholder="Elenca le attività principali, anche in forma grezza…")
    with col2:
        qualifiche = st.text_area("Qualifiche (bozza)", height=220, placeholder="Competenze hard/soft, anni di esperienza, lingue, tool…")
        livelli_studio = st.text_area("Livelli di studio (bozza)", height=120, placeholder="Diploma/laurea, indirizzo, certificazioni…")

    st.subheader("2) Preferenze di stile (opzionali)")
    tone_opts = st.multiselect(
        "Aggiungi sfumature di tono",
        ["chiaro", "concreto", "inclusivo", "autorevole", "accogliente", "orientato all'azione", "formale", "colloquiale"],
        default=["chiaro", "inclusivo", "concreto"],
    )
    add_bullets = st.checkbox("Usa elenchi puntati dove utile", value=True)
    include_benefits = st.text_area("Vantaggi/benefit (opzionale)", placeholder="Ticket, welfare, formazione, smart working…")
    location = st.text_input("Sede (opzionale)")
    contract = st.text_input("Contratto (opzionale)", placeholder="es. Tempo indeterminato, CCNL Metalmeccanico…")

    submitted = st.form_submit_button("Genera annuncio", use_container_width=True)

# -----------------------------
# Prompt, chiamata API e rendering output restano come nella versione precedente
# -----------------------------
