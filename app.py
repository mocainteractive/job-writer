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

/* Contenitore principale più compatto */
.block-container {
    max-width: 1200px;   /* larghezza massima */
    margin: 0 auto;     /* centrato */
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
Siamo la talent company leader al mondo e siamo al tuo fianco per affrontare, insieme, le sfide del mondo del lavoro. #partnerfortalent.
Grazie alla nostra profonda conoscenza del mercato del lavoro, aiutiamo i talenti a costruire una carriera professionale rilevante e supportiamo le aziende nella creazione di un team qualificato e diversificato. Grazie all’attività dei nostri professionisti, uniamo le aspettative di chi cerca e di chi offre lavoro creando solidi rapporti di fiducia che definiscono storie, opportunità e prospettive sempre nuove.
La nostra strategia e i nostri valori guidano la nostra crescita.
Aspiriamo ad essere la talent company più equa e specializzata al mondo. Ci impegniamo a mantenere una cultura equa, guidata dai valori fondamentali che ci contraddistinguono fin dalla nostra nascita.
Offriamo servizi complementari e un interlocutore unico per garantire continuità, risposte tempestive e un’approfondita conoscenza. 
L'uniformità dei nostri processi di selezione e gestione del candidato, comuni in tutto il territorio, ci permettono di reclutare i migliori profili presenti sul mercato.
La nostra strategia Partner for Talent garantisce ai talenti il supporto mirato che richiedono e ai clienti le competenze specializzate e l'esperienza di cui il loro business ha bisogno.
I nostri valori fondamentali fungono da bussola per tutti in Randstad, guidando il nostro comportamento e rappresentando il fondamento della nostra cultura. 
Su questi valori, basiamo il nostro continuo successo e la nostra reputazione di integrità, servizio e professionalità.
Dobbiamo il nostro successo all’eccellenza del servizio prestato, che offre ben più dei requisiti fondamentali del nostro settore.

Svolgiamo il nostro lavoro in modo corretto ed etico, evitando situazioni che potrebbero creare conflitto di interessi.
Non mettiamo in atto condotte di corruzione attiva o passiva, né offriamo o accettiamo regali, ospitalità o altre utilità che potrebbero creare un condizionamento indebito o configurarsi come un comportamento inappropriato. 
Siamo rispettosi. Diamo importanza alle nostre relazioni e trattiamo bene le persone.

Trattiamo gli altri in modo imparziale, con attenzione e rispetto dei diritti umani. Non sono tollerate intimidazioni né molestie di alcun tipo.
Rispettiamo il diritto alla privacy e assicuriamo che le informazioni riservate siano mantenute tali.
Non usiamo impropriamente i beni aziendali, inclusi hardware, software, sistemi e banche dati, per fini personali.

Conosciamo e rispettiamo i principi internazionali dei diritti umani, le leggi che governano la nostra attività, le policy interne del Gruppo e le norme a tutela della concorrenza.
Conosciamo e rispettiamo le leggi sull’insider trading e sull’abuso di mercato.
Assicuriamo che i nostri archivi vengano creati, usati, conservati e distrutti in conformità alla legge.
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
    - Correggere errori, ridondanze e ambiguità, mantenendo la veridicità delle informazioni.
    - Evitare qualsiasi discriminazione (età, genere, etnia, orientamento, stato civile, ecc.).
    - Evidenziare elementi chiave: responsabilità, requisiti, crescita, benefit, luogo e contratto se presenti.
    {bullets_rule}

    Linee guida:
    - Titolo breve (max ~70 caratteri), concreto e inclusivo.
    - Paragrafi concisi (2-4 frasi) e/o elenchi per scansionabilità.
    - Evita gergo interno, acronimi non spiegati, superlativi vuoti.
    - Preferisci verbi attivi ("gestirai", "collaborerai", "implementerai").
    - Aggiungi una call-to-action breve e chiara.

    Output richiesto in JSON valido con le chiavi:
    {{
      "titolo": string,
      "abstract": string,
      "responsabilita": [string, ...],
      "qualifiche": [string, ...],
      "livelli_studio": [string, ...],
      "benefit": [string, ...],
      "dettagli": {{"sede": string, "contratto": string}},
      "annuncio_completo": string
    }}

    {brand_section}
    """)

def build_user_prompt(title: str, descrizione: str, responsabilita: str, qualifiche: str, livelli_studio: str, include_benefits: str, location: str, contract: str) -> str:
    return textwrap.dedent(f"""
    Dati di input grezzi del recruiter:
    - Titolo: {title}
    - Descrizione generale (bozza):\n{descrizione}
    - Responsabilità (bozza):\n{responsabilita}
    - Qualifiche (bozza):\n{qualifiche}
    - Livelli di studio (bozza):\n{livelli_studio}
    - Benefit extra (opzionali):\n{include_benefits}
    - Sede (opzionale): {location}
    - Contratto (opzionale): {contract}

    Istruzioni: arricchisci e normalizza le informazioni in modo realistico ma senza inventare dettagli non forniti; se una sezione è assente, lascia il campo vuoto o suggerisci placeholder tra parentesi quadre.
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
    responsabilita = data.get("responsabilita") or []
    qualifiche = data.get("qualifiche") or []
    livelli = data.get("livelli_studio") or []
    benefit = data.get("benefit") or []
    dettagli = data.get("dettagli") or {}
    full = data.get("annuncio_completo") or ""

    st.header(titolo)
    st.write(abstract)

    cols = st.columns(2)
    with cols[0]:
        st.subheader("Responsabilità")
        for item in responsabilita:
            st.markdown(f"- {item}")
        st.subheader("Qualifiche")
        for item in qualifiche:
            st.markdown(f"- {item}")
    with cols[1]:
        st.subheader("Livelli di studio")
        for item in livelli:
            st.markdown(f"- {item}")
        if benefit:
            st.subheader("Benefit")
            for item in benefit:
                st.markdown(f"- {item}")
        if dettagli:
            st.subheader("Dettagli")
            sede = dettagli.get("sede") or ""
            contratto = dettagli.get("contratto") or ""
            st.markdown(f"**Sede:** {sede}")
            st.markdown(f"**Contratto:** {contratto}")

    st.subheader("Annuncio completo")
    editable = st.text_area("", value=full, height=400)

    st.download_button(
        label="⬇️ Scarica .txt",
        data=editable,
        file_name=f"annuncio_{re.sub(r'[^a-zA-Z0-9]+', '_', titolo.lower())}.txt",
        mime="text/plain",
        use_container_width=True,
    )
    md_export = f"# {titolo}\\n\\n{abstract}\\n\\n## Responsabilità\\n" + "\\n".join([f"- {x}" for x in responsabilita]) + "\\n\\n## Qualifiche\\n" + "\\n".join([f"- {x}" for x in qualifiche]) + "\\n\\n## Livelli di studio\\n" + "\\n".join([f"- {x}" for x in livelli])
    if benefit:
        md_export += "\\n\\n## Benefit\\n" + "\\n".join([f"- {x}" for x in benefit])
    if dettagli:
        md_export += "\\n\\n## Dettagli\\n"
        if dettagli.get("sede"):
            md_export += f"- **Sede:** {dettagli['sede']}\\n"
        if dettagli.get("contratto"):
            md_export += f"- **Contratto:** {dettagli['contratto']}\\n"
    md_export += "\\n\\n---\\n\\n" + editable

    st.download_button(
        label="⬇️ Scarica .md",
        data=md_export,
        file_name=f"annuncio_{re.sub(r'[^a-zA-Z0-9]+', '_', titolo.lower())}.md",
        mime="text/markdown",
        use_container_width=True,
    )

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
            if not raw:
                st.error("Nessuna risposta dal modello.")
            else:
                data = safe_json_loads(raw)
                if not data:
                    st.warning("La risposta non era JSON valido. Mostro il testo grezzo qui sotto.")
                    st.text_area("Risposta grezza", value=raw, height=300)
                else:
                    dettagli = data.get("dettagli") or {}
                    if location and not dettagli.get("sede"):
                        dettagli["sede"] = location
                    if contract and not dettagli.get("contratto"):
                        dettagli["contratto"] = contract
                    data["dettagli"] = dettagli
                    render_output(data)

st.markdown("""
---
**Note privacy e conformità:** non inserire dati personali identificativi nei campi di input. L'app aiuta l'editing; la responsabilità editoriale finale resta al recruiter.
""")
