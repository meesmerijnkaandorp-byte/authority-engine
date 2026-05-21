import streamlit as st
from openai import OpenAI
import time
import re

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v24.0 | The Final Balance", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API-sleutel niet gevonden.")

def count_words(text):
    return len(text.split())

# --- DE GOUDEN STANDAARD (Jouw goedgekeurde lifestyle tekst) ---
LIFESTYLE_BENCHMARK = """
"In een wereld waarin alles sneller lijkt te gaan, groeit de behoefte aan rust... Een opgeruimde omgeving helpt om je hoofd leeg te maken... De slaapkamer speelt hierin een hoofdrol. Het gaat om het gevoel dat de ruimte je ondersteunt."
"""

# --- AGENT PROMPTS ---

ARCHITECT_PROMPT = f"""Jij bent een Hoofdredacteur van een hoogwaardig lifestyle magazine.
Ontwerp een essay-structuur voor {{target}} woorden.

DOEL: Schrijf een diepgaand artikel over de relatie tussen een geordend huis en een rustig hoofd.
REFERENTIE VOOR TOON: {LIFESTYLE_BENCHMARK}

STRICTE OPDRACHT:
1. Plan 5 hoofdstukken (H2). 
2. Hoofdstuk 3 MOET specifiek gaan over de fysieke verankering van orde: hoe een goede {{anchor}} fungeert als het fundament van een opgeruimde slaapkamer.
3. Plan de overige hoofdstukken rondom psychologie, nachtrust en de 'vrijheid van minder'.
4. GEEN prijzen, GEEN maten, GEEN handleidingen.
"""

WRITER_PROMPT = f"""Jij bent een ervaren essayist. Je schrijft voor een publiek dat diepgang zoekt.

STIJLREGELS:
- TOON: Kalm, nuchter en reflectief. 
- VERBODEN WOORDEN: oase, harmonieus, samenspel, ontdek, essentieel, cruciaal, wereld van verschil, beleving, uniek, krachtig.
- EIS: Gebruik concrete, menselijke observaties (bijv. de rust van een lege vloer, de textuur van stof).
- ANKER-EIS: In het toegewezen hoofdstuk MOET je het woord '{{anchor}}' natuurlijk gebruiken.

DOEL: Schrijf minimaal {{section_target}} woorden voor deze sectie.
"""

ASSEMBLER_PROMPT = """Jij bent de eindredacteur. Smeed de teksten aaneen.
1. Zorg dat de overgang van psychologie naar de praktische oplossing (de kast) vloeiend verloopt.
2. Verwijder elke zin die klinkt als 'marketing-praat'.
3. Zorg dat het volume rond de {target} woorden ligt.
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
st.title("🛡️ Authority Engine v24.0")
st.subheader("The Final Balance: Lifestyle Essays with Commercial Integrity")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    word_count_target = st.slider("Target", 600, 1500, 950, step=50)
    
    start_btn = st.button("GENEREER MASTER ASSET")

if start_btn:
    start_time = time.time()
    with st.status("🏗️ Essay wordt opgebouwd...", expanded=True) as status:
        
        # FASE 1: ARCHITECT
        blueprint = call_ai(f"Plan voor {target_url}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, url=target_url, client=client_name, anchor=anchor_text))
        
        # FASE 2: WRITING
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int((word_count_target // 5) + 80)
        
        for i, s in enumerate(sections):
            st.write(f"🖋️ Schrijven aan hoofdstuk {i+1}...")
            section_text = call_ai(f"Sectie: {s}", WRITER_PROMPT.format(section_target=section_target, anchor=anchor_text))
            full_raw_content += f"\n\n## {section_text}"

        # FASE 3: ASSEMBLY
        st.write("✨ Redactionele polijstfase...")
        final_article = call_ai(f"Assemblage:\n{full_raw_content}", ASSEMBLER_PROMPT.format(target=word_count_target), temp=0.4)
        
        # FASE 4: PYTHON LINK INJECTION (Gegarandeerd succes)
        pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
        final_article = pattern.sub(f"[{anchor_text}]({target_url})", final_article, count=1)

        status.update(label=f"✅ Asset gereed in {int(time.time() - start_time)}s", state="complete")

    # OUTPUT
    st.metric("Volume", count_words(final_article))
    st.markdown(final_article)
    st.download_button("Download Asset", final_article, file_name="final_lifestyle_asset.md")
