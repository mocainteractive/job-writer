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

# -----------------------------
# Custom Randstad-like CSS
# -----------------------------
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

/* Contenitore principale più compatto */
.block-container {
    max-width: 1200px;
    margin: 0 auto;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Pulsante Genera annuncio */
.stButton > button {
    background-color: #4D91E1 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.7em 1.4em !important;
    font-size: 1.1em !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: background-color 0.2s ease-in-out !important;
}
.stButton > button:hover {
    background-color: #3C75B5 !important;
    color: white !important;
}

/* Input box e textarea */
.stTextInput input, .stTextArea textarea {
    border-radius: 6px !important;
    border: 1px solid #d9d9d9 !important;
    padding: 0.6em !important;
    background-color: #ffffff !important;
    font-size: 0.95em !important;
}

/* Multiselect */
.stMultiSelect div[data-baseweb="select"] {
    border-radius: 6px !important;
    border: 1px solid #d9d9d9 !important;
}

/* Checkbox */
.stCheckbox label {
    font-size: 0.95em !important;
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
BRAND_VOICE_FALLBACK = """... (testo lungo tone of voice Randstad che già hai) ...""".strip()
brand_text = BRAND_VOICE_FALLBACK

# -----------------------------
# Input form
# -----------------------------
with st.form("job_form", clear_on_submit=False):
    st.subheader("1) Dati annuncio")
    title = st.text_input("Titolo annuncio", placeholder="Es. Addetto/a amministrazione fornitori")

    col1, col2 = st.columns(2)
    with col1:
        descrizione = st.text_area("Descrizione generale (bozza)", height=180)
        responsabilita = st.text_area("Responsabilità (bozza)", height=220)
    with col2:
        qualifiche = st.text_area("Qualifiche (bozza)", height=220)
        livelli_studio = st.text_area("Livelli di studio (bozza)", height=120)

    st.subheader("2) Preferenze di stile (opzionali)")
    tone_opts = st.multiselect(
        "Aggiungi sfumature di tono",
        ["chiaro", "concreto", "inclusivo", "autorevole", "accogliente", "orientato all'azione", "formale", "colloquiale"],
        default=["chiaro", "inclusivo", "concreto"],
    )
    add_bullets = st.checkbox("Usa elenchi puntati dove utile", value=True)
    include_benefits = st.text_area("Vantaggi/benefit (opzionale)")
    location = st.text_input("Sede (opzionale)")
    contract = st.text_input("Contratto (opzionale)", placeholder="es. Tempo indeterminato, CCNL Metalmeccanico…")

    submitted = st.form_submit_button("Genera annuncio", use_container_width=True)

# -----------------------------
# Prompt engineering
# -----------------------------
def build_system_prompt(brand_text: Optional[str], tone_opts: list[str], add_bullets: bool) -> str:
    tone_flags = ", ".join(tone_opts) if tone_opts else "chiaro, professionale"
    bullets_rule = "Usa elenchi puntati dove appropriato." if add_bullets else "Evita elenchi puntati se non indispensabili."
    brand_section = f"\nContesto tone of voice (estratto sito):\n---\n{brand_text}\n---\n"
    return textwrap.dedent(f"""
    Sei un senior recruiter Randstad che redige annunci impeccabili in Italiano. Scrivi in modo {tone_flags}, inclusivo e conforme alle buone pratiche HR italiane.
    Obiettivi:
    - Migliorare chiarezza, impatto e leggibilità.
    - Uniformare stile e terminologia al tone of voice del brand.
    - Evitare qualsiasi discriminazione.
    {bullets_rule}
    Output richiesto in JSON valido con le chiavi: titolo, abstract, responsabilita, qualifiche, livelli_studio, benefit, dettagli, annuncio_completo.
    {brand_section}
    """)

def build_user_prompt(title, descrizione, responsabilita, qualifiche, livelli_studio, include_benefits, location, contract) -> str:
    return textwrap.dedent(f"""
    Dati di input del recruiter:
    - Titolo: {title}
    - Descrizione: {descrizione}
    - Responsabilità: {responsabilita}
    - Qualifiche: {qualifiche}
    - Livelli di studio: {livelli_studio}
    - Benefit: {include_benefits}
    - Sede: {location}
    - Contratto: {contract}
    """)

# -----------------------------
# OpenAI client
# -----------------------------
_client = None
def get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

def call_openai(system_prompt: str, user_prompt: str) -> Optional[str]:
    client = get_client()
    try:
        resp = client.responses.create(
            model=DEFAULT_MODEL,
            temperature=0.3,
            max_output_tokens=1500,
            input=[{"role": "system", "content": system_prompt},{"role": "user", "content": user_prompt}],
        )
        if hasattr(resp, "output_text") and resp.output_text:
            return resp.output_text
        return str(resp)
    except Exception as e:
        st.error(f"Errore API: {e}")
        return None

# -----------------------------
# Helpers
# -----------------------------
def safe_json_loads(txt: str) -> Optional[dict]:
    if not txt:
        return None
    m = re.search(r"\{[\s\S]*\}\s*$", txt)
    candidate = m.group(0) if m else txt
    try:
        return json.loads(candidate)
    except Exception:
        try:
            candidate2 = re.sub(r",(\s*[}\]])", r"\1", candidate)
            return json.loads(candidate2)
        except Exception:
            return None

def render_output(data: dict):
    st.success("Annuncio generato ✔")
    titolo = data.get("titolo") or "(Titolo mancante)"
    abstract = data.get("abstract") or ""
    st.header(titolo)
    st.write(abstract)
    st.subheader("Annuncio completo")
    st.text_area("", value=data.get("annuncio_completo") or "", height=400)

# -----------------------------
# Run
# -----------------------------
if submitted:
    if not title and not any([descrizione, responsabilita, qualifiche, livelli_studio]):
        st.error("Inserisci almeno il titolo o una bozza di contenuto.")
    else:
        with st.spinner("Genero l'annuncio…"):
            sys_prompt = build_system_prompt(brand_text, tone_opts, add_bullets)
            user_prompt = build_user_prompt(title, descrizione, responsabilita, qualifiche, livelli_studio, include_benefits, location, contract)
            raw = call_openai(sys_prompt, user_prompt)
            if raw:
                data = safe_json_loads(raw)
                if data:
                    render_output(data)
                else:
                    st.warning("La risposta non era JSON valido.")
                    st.text_area("Risposta grezza", value=raw, height=300)

st.markdown("""---  
**Note privacy e conformità:** non inserire dati personali identificativi nei campi di input.  
""")
