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
</style>
""", unsafe_allow_html=True)

# =============================
# Header
# =============================
st.markdown("""
<div style="display:flex;align-items:center;justify-content:center;gap:40px;margin-bottom:20px;">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Randstad_Logo.svg/2560px-Randstad_Logo.svg.png" alt="Randstad" style="height:40px;">
  <h1 style="margin:0;font-size:2.2em;">Job Assistant</h1>
  <img src="https://mocainteractive.com/wp-content/uploads/2025/04/cropped-moca_logo-positivo-1.png" alt="Moca" style="height:40px;">
</div>
""", unsafe_allow_html=True)

st.markdown("""
Incolla una **bozza unica** (anche disordinata). L'AI la divide e rifinisce in **Titolo**, **Descrizione generale**, **Responsabilità**, **Qualifiche**, **Livelli di studio** e un **annuncio completo** già pronto, coerente con il *tone of voice Randstad*.
""")

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
Offriamo servizi complementari, processi uniformi sul territorio e selezioniamo i migliori profili presenti sul mercato.
Operiamo in modo etico, nel rispetto delle leggi, dei diritti umani, della privacy e delle norme a tutela della concorrenza; non sono tollerati comportamenti scorretti o discriminatori.
""".strip()

# =============================
# Form (un solo campo)
# =============================
with st.form("single_input_form", clear_on_submit=False):
    st.subheader("Bozza unica")
    raw_blob = st.text_area(
        "Incolla qui qualsiasi informazione sul ruolo (azienda, sede, responsabilità, requisiti, studi, benefit...). Anche in forma libera.",
        height=220,
        placeholder="Esempio: stiamo cercando un macchinista piega-incolla per azienda packaging a Bottanuco (BG)..."
    )

    st.subheader("Preferenze di stile (opzionali)")
    tone_opts = st.multiselect(
        "Sfumature di tono",
        ["chiaro", "concreto", "inclusivo", "autorevole", "accogliente", "orientato all'azione", "formale", "colloquiale"],
        default=["chiaro", "inclusivo", "concreto"],
    )

    submitted = st.form_submit_button("🚀 Genera annuncio", use_container_width=True)

# =============================
# Prompt engineering
# =============================
def build_system_prompt(brand_text: str, tone_opts: list[str]) -> str:
    tone_flags = ", ".join(tone_opts) if tone_opts else "chiaro, professionale"

    return textwrap.dedent(f"""
    Sei un senior recruiter Randstad. Scrivi in Italiano in modo {tone_flags}, inclusivo e conforme alle buone pratiche HR.

    Requisiti di stile IMPORTANTI:
    - **Titolo**: brevissimo e oggettivo, indica **solo la mansione** (esempi: "Macchinista piega-incolla", "Addetto amministrazione fornitori"). Niente slogan o aggettivi superflui.
    - **Descrizione generale (abstract)**: **solo testo discorsivo** di 3–5 frasi, senza elenchi puntati.
    - **Responsabilità**: elenchi puntati sintetici (max 6–8), con verbi attivi.
    - **Qualifiche**: elenchi puntati sintetici (max 6–8), solo requisiti essenziali.
    - **Livelli di studio**: array con eventuali titoli/qualifiche/certificazioni.
    - **Benefit**: se presenti.
    - **CTA**: chiusura breve e chiara.
    - Evita gergo interno, acronimi non spiegati e superlativi vuoti.
    - Mantieni fedeltà ai dati forniti; se un elemento manca, usa il placeholder [dato non disponibile].

    Output richiesto in **JSON valido** (senza ``` né testo extra) con le chiavi:
    {{
      "titolo": string,
      "abstract": string,                # paragrafo discorsivo
      "responsabilita": [string, ...],   # bullet sintetici
      "qualifiche": [string, ...],       # bullet sintetici
      "livelli_studio": [string, ...],
      "benefit": [string, ...],
      "dettagli": {{ "sede": string, "contratto": string }},
      "annuncio_completo": string        # testo pronto, con mix di narrazione + punti dove serve
    }}

    Contesto tone of voice:
    ---
    {brand_text}
    ---
    """)

def build_user_prompt(raw_blob: str) -> str:
    return textwrap.dedent(f"""
    Bozza unica fornita dal recruiter (grezza, da ripulire e strutturare):
    ---
    {raw_blob}
    ---
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
        # Provo a forzare JSON nativo
        try:
            resp = client.responses.create(
                model=DEFAULT_MODEL,
                temperature=0.3,
                max_output_tokens=1500,
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
                max_output_tokens=1500,
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
    # rimuove eventuali fence ```json
    s = re.sub(r"^\s*```(?:json|JSON)?\s*\n", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\n?\s*```$", "", s)
    m = re.search(r"\{[\s\S]*\}\s*$", s)
    candidate = m.group(0) if m else s
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
    responsabilita = data.get("responsabilita") or []
    qualifiche = data.get("qualifiche") or []
    livelli = data.get("livelli_studio") or []
    benefit = data.get("benefit") or []
    dettagli = data.get("dettagli") or {}
    full = data.get("annuncio_completo") or ""

    st.header(titolo)
    st.write(abstract)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Responsabilità")
        for it in responsabilita:
            st.markdown(f"- {it}")
        st.subheader("Qualifiche")
        for it in qualifiche:
            st.markdown(f"- {it}")
    with c2:
        st.subheader("Livelli di studio")
        for it in livelli:
            st.markdown(f"- {it}")
        if benefit:
            st.subheader("Benefit")
            for it in benefit:
                st.markdown(f"- {it}")
        if dettagli:
            st.subheader("Dettagli")
            st.markdown(f"**Sede:** {dettagli.get('sede','')}")
            st.markdown(f"**Contratto:** {dettagli.get('contratto','')}")

    st.subheader("Annuncio completo")
    editable = st.text_area("", value=full, height=380)

    st.download_button(
        label="⬇️ Scarica .txt",
        data=editable,
        file_name=f"annuncio_{re.sub(r'[^a-zA-Z0-9]+','_', titolo.lower())}.txt",
        mime="text/plain",
        use_container_width=True,
    )

# =============================
# Run
# =============================
if submitted:
    if not raw_blob.strip():
        st.error("Incolla almeno qualche riga nella bozza.")
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
                    render_output(data)

st.markdown("""
---
**Note privacy e conformità:** non inserire dati personali identificativi nella bozza. L'app aiuta l'editing; la responsabilità editoriale finale resta al recruiter.
""")
