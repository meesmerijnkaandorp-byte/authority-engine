import streamlit as st
from openai import OpenAI

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Content Engine v1.4 | DEEP NARRATIVE", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("API Key niet gevonden. Controleer je Streamlit Secrets.")

def count_words(text):
    return len(text.split())

# --- SYSTEM PROMPTS (V14 - ANTI-FRAGMENTATIE UPDATE) ---

WRITER_PROMPT = """
Jij bent een Senior Journalist voor diepgaande publicaties zoals The Economist of De Correspondent. Je schrijft geen oppervlakkige SEO-lijstjes, maar autoritaire essays die de lezer meezuigen in een verhaal.

STRICTE OPDRACHT TEGEN FRAGMENTATIE:
1. GEEN HEADER-ITIS: Gebruik maximaal 3 tot 4 H2-tussenkoppen voor het hele artikel. Gebruik H3-koppen alleen als het strikt noodzakelijk is voor een technisch onderscheid. 
2. NARRATIEVE FLOW: Gebruik overgangszinnen ("Connective Tissue") om van het ene aspect naar het andere te gaan binnen één sectie. Een nieuwe alinea betekent niet automatisch een nieuwe kop.
3. ALINEA-GEWICHT: Elke alinea moet substantieel zijn (minimaal 6 tot 10 regels). Ontwikkel één complex idee per alinea in plaats van drie simpele feitjes.
4. WOORDENAANTAL: Je moet het doel halen door DIEPGANG en ANALYSE, niet door meer koppen toe te voegen.

SCHRIJFSTIJL (ZERO-TRACE):
- Varieer extreem in zinslengte. Gebruik af en toe een zeer korte zin voor impact tussen langere, complexe zinnen door.
- Vermijd de 'AI-lijstjes-structuur'. Als je een opsomming gebruikt, maak er dan een lopende tekst van of gebruik bullets alleen voor data-punten, niet voor de kern van je betoog.
- De links moeten verweven zijn in een vloeiende redenering, niet als een 'extraatje' aan het einde van een blok.

DEFINITION OF DONE:
- SEO Metadata bovenaan.
- # H1 (Prikkelend).
- ## H2 (Maximaal 4 stuks, zeer rijk gevuld met tekst).
- De tekst moet aanvoelen als een 'long-read' die je in een papieren magazine zou lezen.
"""

AUDITOR_PROMPT = """
Jij bent een meedogenloze Hoofdredacteur die allergisch is voor 'versnipperde' teksten. Als een tekst eruitziet als een lijst met headers, keur je hem direct af.

JOUW ANALYSE-KADER:
1. HEADER-CHECK: Tel de koppen. Zijn er meer dan 5 tussenkoppen? SCORE = 0. Dwing de writer om secties samen te voegen tot één vloeiend verhaal.
2. ALINEA-CHECK: Zijn alinea's korter dan 4 regels? Score < 50. Dit is 'AI-slop'. Een expert heeft meer te vertellen.
3. NARRATIEVE LIJN: Loopt het verhaal logisch door zonder de hulp van koppen? Zoek naar overgangswoorden (Echter, Dit impliceert, In tegenstelling tot).
4. WOORDEN-DICTATUUR: Tekort aan woorden = Afgekeurd.

STRIKTE OUTPUT TEMPLATE:
## 📊 AUTHORITY SCORE: [0-100]
### 📏 WOORDEN-CHECK: [Aantal] vs [Doel]

### 🚩 FRAGMENTATIE-ALARM
- [Noem plekken waar de tekst te veel 'opgebroken' is en waar headers verwijderd moeten worden].

### 🛠 DE NARRATIEVE FIX
- VERWIJDER HEADER: "[De specifieke H3 die weg moet]"
- VERBINDINGSSUGGESTIE: [Hoe kan de writer de twee blokken tekst vloeiend aan elkaar schrijven?]

### ✍️ MASTERCLASS REWRITE
[Herschrijf een groot blok tekst (minimaal 200 woorden) zonder één enkele tussenkop te gebruiken, om te laten zien hoe narratieve flow werkt.]
"""

# --- FUNCTIES ---
def generate_content(prompt, system_instruction):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🛡️ Zero-Trace Authority Engine | V14 Deep Narrative")
st.markdown("Geoptimaliseerd voor 2026: Geen versnipperde AI-teksten, maar echte diepgang.")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", placeholder="Bijv. Table du Sud")
    target_domain = st.text_input("Platform", placeholder="Bijv. ad.nl")
    
    st.divider()
    word_count_target = st.slider("Target Woorden", 300, 1500, 750, step=50)
    
    st.divider()
    link_1 = st.text_input("Link 1 (URL)")
    anchor_1 = st.text_input("Anchor 1")
    link_2 = st.text_input("Link 2 (Optioneel)")
    anchor_2 = st.text_input("Anchor 2")
    
    subject = st.text_area("Insteek (Optioneel)")
    
    start_btn = st.button("GENEREER DEEP-NARRATIVE CONTENT", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Verplichte velden missen.")
    else:
        subject_content = subject if subject.strip() else f"Schrijf een autoritair essay voor {target_domain} over een relevant onderwerp voor {client_name}."
        
        with st.status("🚀 Systeem bouwt narratieve structuur...", expanded=True) as status:
            # RONDE 1
            st.write("🖋️ **Titan_Writer** schrijft eerste diepgaande draft...")
            briefing = f"KLANT: {client_name}\nPLATFORM: {target_domain}\nDOEL: {word_count_target} woorden\nLINK: {link_1} ({anchor_1})\nONDERWERP: {subject_content}"
            draft = generate_content(briefing, WRITER_PROMPT)
            c1 = count_words(draft)
            
            # RONDE 2
            st.write(f"🧐 **Inquisitor_Auditor** controleert op fragmentatie...")
            audit_feedback = generate_content(f"DOEL: {word_count_target}. HUIDIG: {c1}. TEKST:\n\n{draft}", AUDITOR_PROMPT)
            
            # RONDE 3
            st.write("✨ **Titan_Writer** smeedt alinea's aaneen...")
            final_briefing = f"Herschrijf de tekst. De Auditor haat je headers. Maak er een vloeiend verhaal van van minimaal {word_count_target} woorden. Gebruik de 'Verbindingssuggesties' van de Auditor.\n\nAUDIT:\n{audit_feedback}"
            final_text = generate_content(final_briefing, WRITER_PROMPT)
            c_final = count_words(final_text)
            
            status.update(label=f"✅ Klaar: {c_final} woorden in narratieve flow.", state="complete")

        t1, t2, t3 = st.tabs(["📄 Publicatie", "🔍 Audit", "📝 Log"])
        with t1:
            st.metric("Aantal woorden", f"{c_final} woorden", delta=int(c_final - word_count_target))
            st.markdown(final_text)
        with t2:
            st.markdown(audit_feedback)
        with t3:
            st.text_area("Draft V1", draft, height=400)
