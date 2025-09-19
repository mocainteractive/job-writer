# Randstad Job Writer

Tool Streamlit che aiuta i recruiter a generare/rifinire le offerte di lavoro:
- Riscrittura testo nel tone of voice 
- Campi strutturati (ruolo, sede, RAL, contratto, esperienza, responsabilità, qualifiche)
- Controlli di qualità (chiarezza, lunghezza, inclusività)
- Esportazione in Excel

## Deploy rapido
1. Carica `app.py` e `requirements.txt`.
2. Su Streamlit Cloud: Deploy → collega questa repo → `main` + `app.py`.
3. In **Secrets** aggiungi:
  OPENAI_API_KEY = "sk-..."
  ACCESS_CODE = "moca-app" # opzionale per gate d’accesso


## Requisiti
Vedi `requirements.txt`.

## Note
I segreti non stanno in repo: configurali su Streamlit (Settings → Secrets).
