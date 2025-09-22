import os
import re
import json
import textwrap
from typing import Optional

import streamlit as st

# =============================
# App Config
# =============================
st.set_page_config(
    page_title="Job Assistant",
    page_icon="https://mocainteractive.com/wp-content/uploads/2025/04/cropped-moca-instagram-icona-1.png",
    layout="wide",
)

# =============================
# CSS (look & feel Randstad)
# =============================
st.markdown("""
<style>
body { background-color:#F7F7F7; font-family:"Open Sans",sans-serif; }
h1,h2,h3,h4 { font-weight:600; color:#001C54; }
/* container più compatto */
.block-container { max-width:1200px; margin:0 auto; padding:2rem 0; }
/* pulsanti */
.stButton > button{
  background:#0057B8 !important; color:#fff !important; border:none !important;
  border-radius:6px !important; padding:.6em 1.2em !important; font-size:1.1em !important; font-weight:600 !important;
  transition: background-color .2s ease;
}
.stButton > button:hover{ background:#004494 !important; }
/* input */
.stTextArea textarea, .stTextInput input{
  border-radius:4px !important; border:1px solid #d9d9d9 !important; padding:.6em !important; background:#fff !important;
  transition:border-color .2s ease, box-shadow .2s ease;
}
.stTextArea textarea:hover, .stTextInput input:hover{ border-color:#bfbfbf !important; }
.stTextArea textarea:focus, .stTextInput input:focus{
  border-color:#0057B8 !important; box-shadow:0 0 0 1px #0057B8 !important; outline:none !important;
}
/* chips multiselect */
.stMultiSelect div[data-baseweb="select"]{ border-radius:6px; border:1px solid #d9d9d9; }
.small-note { color:#666; font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

# =============================
# Header
# =============================
st.markdown("""
<div style="display:flex;align-items:center;justify-content:center;gap:40px;margin-bottom:10px;">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Randstad_Logo.svg/2560px-Randstad_Logo.svg.png" alt="Randstad" style="height:40px;">
  <h1 style="margin:0;font-size:2.2em;">Job Assistant</h1>
  <img src="https://mocainteractive.com/wp-content/uploads/2025/04/cropped-moca_logo-positivo-1.png" alt="Moca" style="height:40px;">
</div>
""", unsafe_allow_html=True)

st.markdown(
    "Inserisci qui tutte le informazioni relative all'offerta. "
    "L'AI genererà i campi pronti da copiare: **DESCRIZIONE GENERALE • RESPONSABILITÀ • QUALIFICHE • LIVELLO DI STUDIO**"
)

# =============================
# Config & brand voice
# =============================
DEFAULT_MODEL = "gpt-4o-mini"
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.warning("⚠️ Imposta OPENAI_API_KEY in Secrets o come variabile d’ambiente.")

BRAND_VOICE = """
siamo randstad, il tuo partner nel mondo del lavoro.
Siamo la talent company leader al mondo e siamo al tuo fianco per affrontare, insieme, le sfide del mondo del lavoro. #partnerfortalent.
Grazie alla nostra profonda conoscenza del mercato del lavoro, aiutiamo i talenti a costruire una carriera professionale rilevante e supportiamo le aziende nella creazione di un team qualificato e diversificato.
La nostra strategia e i nostri valori guidano la nostra crescita: cultura equa, integrità, servizio e professionalità.
Offriamo processi uniformi sul territorio e selezioniamo i migliori profili presenti sul mercato.
Operiamo in modo etico, nel rispetto delle leggi, dei diritti umani, della privacy e delle norme a tutela della concorrenza; non sono tollerati comportamenti scorretti o discriminatori.
""".strip()

# =============================
# Form (input minimo, etichetta nascosta)
# =============================
with st.form("single_input_form", clear_on_submit=False):
    raw_blob = st.text_area(
        label="",  # nessun testo visibile
        height=220,
        placeholder="Incolla qui appunti/email/vecchio annuncio: azienda, sede, responsabilità, requisiti, titoli di studio…",
        label_visibility="collapsed",
    )

    st.subheader("Preferenze di stile (opzionali)")
    tone_opts = st.multiselect(
        "Sfumature di tono",
        ["chiaro", "concreto", "inclusivo", "autorevole", "accogliente", "orientato all'azione", "formale", "colloquiale"],
        default=["chiaro", "inclusivo", "concreto"],
    )
    st.caption("Le sfumature servono solo a rifinire la resa; i campi di output restano 4 e invariati.")

    submitted = st.form_submit_button("🚀 Genera annuncio", use_container_width=True)

# =============================
# Prompt engineering
# =============================
def build_system_prompt(brand_text: str, tone_opts: list[str]) -> str:
    tone_flags = ", ".join(tone_opts) if tone_opts else "chiaro, professionale"
    return textwrap.dedent(f"""
    Sei un senior recruiter Randstad. Scrivi in Italiano in modo {tone_flags}, inclusivo e conforme alle buone pratiche HR.

    REGOLE OBBLIGATORIE DEL FORMATO:
    - Restituisci **ESCLUSIVAMENTE** le seguenti quattro chiavi, niente altro:
      1) "descrizione_generale"  -> testo discorsivo (3–6 frasi), **nessun elenco puntato**.
      2) "responsabilita"        -> elenco puntato sintetico (max 6–8 voci) con verbi attivi.
      3) "qualifiche"            -> elenco puntato sintetico (max 6–8 voci) con requisiti essenziali.
      4) "livello_di_studio"     -> elenco breve (titoli di studio/qualifiche/certificazioni).
    - Non includere altri campi (niente titolo, benefit, dettagli, annuncio completo, ecc.).
    - Mantieni fedeltà ai dati forniti; se un elemento è assente scrivi una voce con il placeholder "[dato non disponibile]".
    - IMPORTANTE: restituisci **SOLO JSON valido**, senza ``` e senza testo extra.

    Contesto tone of voice (estratto sito):
    ---
    {brand_text}
    ---
    """)

def build_user_prompt(raw_blob: str) -> str:
    return textwrap.dedent(f"""
    Testo grezzo fornito dal recruiter (da ripulire e strutturare):
    ---
    {raw_blob}
    ---

    Output atteso (solo queste chiavi):
    {{
      "descrizione_generale": string,
      "responsabilita": [string, ...],
      "qualifiche": [string, ...],
      "livello_di_studio": [string, ...]
    }}
    """)

# =============================
# OpenAI client (una sola chiamata)
# =============================
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
        # Preferenza: JSON nativo
        try:
            resp = client.responses.create(
                model=DEFAULT_MODEL,
                temperature=0.3,
                max_output_tokens=1200,
                response_format={"type": "json_object"},
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except Exception:
            # Fallback se response_format non è supportato
            resp = client.responses.create(
                model=DEFAULT_MODEL,
                temperature=0.3,
                max_output_tokens=1200,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

        if hasattr(resp, "output_text") and resp.output_text:
            return resp.output_text
        return str(resp)
    except Exception as e:
        st.error(f"Errore API: {e}")
        return None

# =============================
# Helpers
# =============================
def safe_json_loads(txt: str) -> Optional[dict]:
    if not txt:
        return None
    s = txt.strip()
    # Rimuove eventuali fence ```json
    s = re.sub(r"^\s*```(?:json|JSON)?\s*\n", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\n?\s*```$", "", s)
    # Prende il primo blocco {...}
    m = re.search(r"\{[\s\S]*\}\s*$", s)
    candidate = m.group(0) if m else s
    try:
        return json.loads(candidate)
    except Exception:
        try:
            candidate2 = re.sub(r",(\s*[}\]])", r"\1", candidate)  # rimuove virgole finali
            return json.loads(candidate2)
        except Exception:
            return None

# =============================
# UI render (tutto testo, niente textarea duplicate)
# =============================
def render_output(data: dict):
    st.success("Annuncio generato ✔")

    descrizione_generale = data.get("descrizione_generale") or ""
    responsabilita = data.get("responsabilita") or []
    qualifiche = data.get("qualifiche") or []
    livello_di_studio = data.get("livello_di_studio") or []

    # DESCRIZIONE GENERALE (TESTO, niente box)
    st.subheader("DESCRIZIONE GENERALE")
    st.markdown(descrizione_generale)

    # RESPONSABILITÀ (solo elenco)
    st.subheader("RESPONSABILITÀ")
    for it in responsabilita:
        st.markdown(f"- {it}")

    # QUALIFICHE (solo elenco)
    st.subheader("QUALIFICHE")
    for it in qualifiche:
        st.markdown(f"- {it}")

    # LIVELLO DI STUDIO (solo elenco)
    st.subheader("LIVELLO DI STUDIO")
    for it in livello_di_studio:
        st.markdown(f"- {it}")

# =============================
# Run
# =============================
if submitted:
    if not raw_blob.strip():
        st.error("Inserisci almeno qualche riga di bozza.")
    else:
        with st.spinner("Genero l'annuncio…"):
            sys_prompt = build_system_prompt(BRAND_VOICE, tone_opts)
            user_prompt = build_user_prompt(raw_blob)
            raw = call_openai(sys_prompt, user_prompt)
            if not raw:
                st.error("Nessuna risposta dal modello.")
            else:
                data = safe_json_loads(raw)
                if not data:
                    st.warning("La risposta non era JSON valido. Mostro il testo grezzo qui sotto.")
                    st.text_area("Risposta grezza", value=raw, height=300)
                else:
                    # Mantieni solo le 4 chiavi richieste; se mancano, crea placeholder
                    data = {
                        "descrizione_generale": data.get("descrizione_generale") or "[dato non disponibile]",
                        "responsabilita": data.get("responsabilita") or ["[dato non disponibile]"],
                        "qualifiche": data.get("qualifiche") or ["[dato non disponibile]"],
                        "livello_di_studio": data.get("livello_di_studio") or ["[dato non disponibile]"],
                    }
                    render_output(data)

st.markdown("""
---
**Note privacy e conformità:** non inserire dati personali identificativi nella bozza. L'app aiuta l'editing; la responsabilità editoriale finale resta al recruiter.
""")
