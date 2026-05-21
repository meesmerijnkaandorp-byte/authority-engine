import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v32.0 | The Topic Sentinel", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

def count_words(text):
    return len(text.split())

# --- DE REDACTIONELE WET ---
STRICT_TOPIC_LOCK = """
STRICTE EIS: Het artikel MOET gaan over het fysieke product/onderwerp van de URL: {url}.
De publisher ({publisher}) bepaalt alleen de TOON (nuchter, direct), maar NOOIT het onderwerp. 
Schrijf GEEN metadata of analyses OVER de publisher zelf.
"""

# --- AGENT PROMPTS ---

# 1. De Topic Analyzer (Dwingt focus af)
ANALYZER_PROMPT = """Analyseer deze URL: {url}. 
Wat is het exacte fysieke product of de dienst? 
Antwoord in maximaal 5 woorden. Dit is je HEILIGE ONDERWERP."""

# 2. De Architect (Plant op basis van Topic Lock)
ARCHITECT_PROMPT = """Jij bent een Content Planner. Ontwerp een blueprint voor {target} woorden.
ONDERWERP: {topic}
STIJL: Nuchtere lifestyle-journalistiek voor {publisher}.

EISEN:
- 4 Hoofdstukken (H2).
- Geen politiek, geen meta-analyse van de media.
- Focus op de psychologie van orde en de praktische kant van {topic}.
"""

# 3. De Writer (Gedisciplineerd Schrijver)
WRITER_PROMPT = """Jij bent een nuchtere tekstschrijver. 
ONDERWERP: {topic}
STIJL: {publisher}-stijl (direct, wars van bullshit, geen AI-clichés).

EISEN:
- Schrijf sectie {n}: {section_title}.
- Gebruik GEEN woorden als: oase, essentieel, cruciaal, wereld van verschil.
- Focus op de realiteit: materiaal, ruimte, frustratie, oplossing.
- TARGET: {section_target} woorden.
"""

# 4. De Auditor (Kwaliteitscontroleur)
AUDITOR_PROMPT = """Jij bent een genadeloze eindredacteur. 
Controleer de tekst op:
1. GAAT HET OVER {topic}? (Indien nee: AFKEUREN).
2. IS HET GEEN POLITIEK GEBABBEL? (Indien ja: AFKEUREN).
3. IS DE LINK [{anchor}]({url}) AANWEZIG?

Smeed de tekst aaneen tot een vloeiend geheel van {target} woorden.
Voeg Title, Meta (max 155 tekens) en Slug toe.
"""

# --- AI ENGINE ---
def call_ai(prompt, system_instruction, temp=0.7):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🛡️ Authority Engine v32.0")
st.subheader("The Topic Sentinel: Kwaliteit & Focus boven Snelheid")

with st.sidebar:
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Anker", value="kledingkast")
    publisher_name = st.text_input("Publisher", value="Dagelijkse Standaard")
    word_count_target = st.slider("Target", 600, 1500, 950, step=50)
    start_btn = st.button("EXECUTE QUALITY PRODUCTION", type="primary")

if start_btn:
    start_time = time.time()
    with st.status("🏗️ Productie-cyclus gestart (Deep-Focus Mode)...", expanded=True) as status:
        
        # STAP 1: TOPIC LOCK
        st.write("🔍 Stap 1: Onderwerp vergrendelen...")
        topic = call_ai(f"Wat is het onderwerp van {target_url}?", ANALYZER_PROMPT.format(url=target_url))
        st.info(f"Onderwerp vergrendeld op: **{topic}**")
        
        # STAP 2: ARCHITECT
        st.write("📐 Stap 2: Architectuur ontwerpen...")
        blueprint = call_ai(f"Maak plan voor {topic}", ARCHITECT_PROMPT.format(target=word_count_target, topic=topic, publisher=publisher_name))
        
        # STAP 3: WRITING (SEQUENTIAL)
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = (word_count_target // 4)
        
        for i, s in enumerate(sections):
            st.write(f"🖋️ Stap 3.{i+1}: Schrijven over {topic}...")
            # We vertragen de AI hier bewust door meer instructies te geven
            section_text = call_ai(f"Schrijf: {s}", WRITER_PROMPT.format(n=i+1, topic=topic, section_title=s, section_target=section_target, publisher=publisher_name))
            full_raw_content += f"\n\n## {section_text}"
            time.sleep(1) # Geforceerde rust voor stabiliteit

        # STAP 4: AUDIT & ASSEMBLY
        st.write("✨ Stap 4: Finale Audit & Link-injectie...")
        final_article = call_ai(f"Eindredactie:\n{full_raw_content}", AUDITOR_PROMPT.format(target=word_count_target, topic=topic, anchor=anchor_text, url=target_url), temp=0.4)
        
        # PYTHON LINK INJECTION (Backup)
        if f"]({target_url})" not in final_article:
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            final_article = pattern.sub(f"[{anchor_text}]({target_url})", final_article, count=1)

        duration = int(time.time() - start_time)
        status.update(label=f"✅ Productie voltooid in {duration}s", state="complete")

    # OUTPUT
    st.metric("Gerealiseerd Volume", count_words(final_article))
    st.markdown(final_article)
    st.download_button("Download Asset", final_article, file_name="asset.md")
