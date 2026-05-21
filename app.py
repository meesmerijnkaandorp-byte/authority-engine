import streamlit as st
from openai import OpenAI
import time
import re

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v23.0 | Lifestyle Narrative", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API-sleutel niet gevonden.")

def count_words(text):
    return len(text.split())

# --- DE NIEUWE BENCHMARK (Jouw goedgekeurde tekst als referentie) ---
LIFESTYLE_BENCHMARK = """
"In een wereld waarin alles sneller lijkt te gaan, groeit de behoefte aan rust. Werk stapelt zich op, agenda’s lopen over... Je huis fungeert als tegenwicht voor de drukte buiten. Een opgeruimde omgeving helpt om je hoofd leeg te maken."
"""

# --- AGENT PROMPTS ---

ARCHITECT_PROMPT = f"""Jij bent een Hoofdredacteur van een lifestyle magazine. 
Ontwerp een essay-structuur voor {{target}} woorden. 

REFERENTIE: Gebruik dit als de absolute standaard voor toon en diepgang:
{LIFESTYLE_BENCHMARK}

STRICTE RICHTLIJNEN:
1. GEEN PRODUCTGEGEVENS: Praat NOOIT over afmetingen (cm), prijzen (euro's) of montagetips.
2. THEMA: Focus op de psychologie van wonen. Waarom geeft orde rust? Hoe beïnvloedt je slaapkamer je mindset?
3. ROL VAN KLANT: Noem {{client}} alleen als facilitator van deze rust.
4. STRUCTUUR: Plan 4 beschouwende hoofdstukken (H2) die een verhaal vertellen, geen gids.
"""

WRITER_PROMPT = f"""Jij bent een essayist. Je schrijft reflectieve teksten over modern leven en wonen.

STIJLREGELS:
- TOON: Kalm, volwassen, invoelend. Geen marketing-enthousiasme.
- VERBODEN: 'oase', 'essentieel', 'cruciaal', 'samenspel', 'ontdek', 'wereld van verschil', 'bij het aanschaffen van', 'afmetingen', 'prijs-kwaliteit'.
- METHODE: Schrijf over emoties en mentale ruimte. 
- ZINSBOUW: Varieer in lengte. Gebruik korte zinnen voor nadruk.

DOEL: Schrijf minimaal {{section_target}} woorden voor deze sectie.
"""

ASSEMBLER_PROMPT = """Jij bent de eindredacteur. Smeed de teksten aaneen tot een vloeiend essay van {target} woorden.

TAKEN:
1. VERWIJDER PRODUCT-SLOP: Als je leest over 'betaalbare opties' of 'montage', verwijder het.
2. FLOW: Zorg dat het artikel leest als een opiniestuk of een diepgaand blog.
3. SEO: Genereer Metadata (Title, Meta Description, Slug) die aansluit bij lifestyle en rust.
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
st.title("🛡️ Authority Engine v23.0")
st.subheader("Lifestyle Narrative Engine | Psychology over Product")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Anker", value="kledingkast")
    word_count_target = st.slider("Target", 600, 1500, 900, step=50)
    
    start_btn = st.button("GENEREER LIFESTYLE ESSAY")

if start_btn:
    start_time = time.time()
    with st.status("🏗️ Essay wordt geweven...", expanded=True) as status:
        
        # FASE 1: ARCHITECT
        blueprint = call_ai(f"Essay voor {target_url}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, url=target_url, client=client_name))
        
        # FASE 2: WRITING
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int((word_count_target // 4) + 100)
        
        for i, s in enumerate(sections):
            st.write(f"🖋️ Essayist schrijft hoofdstuk {i+1}...")
            section_text = call_ai(f"Sectie: {s}", WRITER_PROMPT.format(section_target=section_target, client=client_name))
            full_raw_content += f"\n\n## {section_text}"

        # FASE 3: ASSEMBLY
        st.write("✨ Redactie op flow en toon...")
        final_article = call_ai(f"Assemblage:\n{full_raw_content}", ASSEMBLER_PROMPT.format(target=word_count_target), temp=0.4)
        
        # FASE 4: PYTHON LINK INJECTION
        # We zoeken de eerste keer dat de ankertekst voorkomt (meestal rond 30-50% van de tekst)
        # Voor lifestyle doen we het niet in de eerste alinea om de 'vibe' niet te breken.
        pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
        final_article = pattern.sub(f"[{anchor_text}]({target_url})", final_article, count=1)

        status.update(label=f"✅ Essay gereed in {int(time.time() - start_time)}s", state="complete")

    # OUTPUT
    st.metric("Volume", count_words(final_article))
    st.markdown(final_article)
    st.download_button("Download", final_article, file_name="lifestyle_asset.md")
