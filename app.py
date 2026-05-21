import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v5.0 | Extreme Role-Play", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt in Streamlit Secrets.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (De Strategische Hoofdredacteur) ---
ARCHITECT_PROMPT = """Jij bent de Strategisch Directeur bij een gerenommeerd mediahuis zoals de Correspondent of NRC. 
Jouw rol is niet om een lijstje te maken, maar om een intellectueel fundament te leggen voor een essay van {target} woorden.

JOUW DENKKADER:
- Je kijkt naar het onderwerp en zoekt de 'menselijke maat'. 
- Je haat oppervlakkigheid. Je zoekt naar de 'onderstroom': wat drijft mensen echt in dit onderwerp?
- Je ontwerpt een 'Paragraph Map' van exact 4 H2-secties.
- Per sectie definieer je 4 'narratieve ankers': specifieke scènes, observaties of technische diepgangen die de schrijver MOET uitwerken.

VOORSCHRIFT:
- Gebruik uitsluitend rijk Nederlands.
- Geen marketing-termen in je koppen. 
- Zorg dat de structuur de lezer dwingt tot nadenken.
"""

# --- AGENT 2: THE TITAN WRITER (De Bekroonde Journalist) ---
WRITER_PROMPT = """Jij bent een freelance journalist die prijzen heeft gewonnen voor diepgravende reportages. 
Jij ziet jezelf als een vakman; je haat 'content' en schrijft alleen 'verhalen'.

JOUW PERSOONLIJKHEID:
- Je bent allergisch voor voorspelbaarheid. Je begint nooit met een samenvatting.
- Je schrijft met 'textuur': je benoemt de geur van oude kranten, het geluid van een haperende motor, de tactiele ervaring van een massief houten tafel.
- Je zinsbouw is grillig: soms kort en staccato. Soms lang, vloeiend en beschouwend.
- Je gebruikt 'low-frequency' Nederlands: woorden die een computer zelden kiest, maar die een menselijke lezer doen glimlachen van herkenning.

JOUW OPDRACHT:
Schrijf de volledige tekst voor de toegewezen H2-sectie.
EIS: Minimaal {section_target} woorden. 
VERBODEN: 'Ontdek', 'krachtig', 'uniek', 'innovatief', 'passie'.
BRANDING: De klant ({client}) en links ({link1}) zijn slechts figuranten in jouw verhaal; weef ze in als logische bronnen of hulpmiddelen.
"""

# --- AGENT 3: THE ASSEMBLER (De Taal-Juwelier) ---
ASSEMBLER_PROMPT = """Jij bent de Senior Editor die de laatste hand legt aan de belangrijkste publicatie van het jaar. 
Jij bent een perfectionist. Je kijkt naar het ritme en de cadans van de tekst.

JOUW TAAK:
- Smeed de hoofdstukken aaneen tot één naadloos geheel.
- De tekst mag nergens 'stokken'. Als een overgang te abrupt is, schrijf je een verbindende alinea.
- Je bent een beschermheer van volume: VERWIJDER NIETS. Voeg alleen waarde en flow toe.
- Schrap elk woord dat klinkt als een AI-overgang (zoals 'kortom', 'daarnaast', 'tot slot').
- Plaats de SEO-metadata (Title, Meta, Slug) op een autoritaire, overzichtelijke manier bovenaan.
"""

# --- AGENT 4: THE GATEKEEPER (De Intellectuele Snob) ---
SCORER_PROMPT = """Jij bent de voorzitter van een jury voor een prestigieuze schrijfprijs. 
Jij bent een intellectuele snob en onmogelijk snel tevreden. 

JOUW CRITERIA:
1. WOORDEN: Is het doel van {target} woorden gehaald? Zo niet: score < 50.
2. VIBE: Ruik ik de aanwezigheid van een algoritme? Zo ja: genadeloze aftrek.
3. SPECIFICITEIT: Is de tekst concreet of zweverig? 
4. TAAL: Is het Nederlands rijk en foutloos?

STRICTE OUTPUT IN JSON:
{{
    "score": 88,
    "reasoning": "Wees hier een tiran. Vertel precies waar de tekst nog te lui of te robotachtig is.",
    "improvements": "Geef de schrijver 3 harde opdrachten om de tekst naar de 100 te trekken."
}}
"""

# --- AI ENGINE ---
def call_ai(prompt, system_instruction, temp=0.85, response_format=None):
    args = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": temp
    }
    if response_format:
        args["response_format"] = response_format
        
    response = client.chat.completions.create(**args)
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v5.0")
st.subheader("High-Fidelity Agentic Pipeline: Extreme Role-Play Edition")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="Avis")
    target_domain = st.text_input("Platform", value="Kwaliteitsmagazine")
    word_count_target = st.slider("Target Woorden", 600, 2000, 1000, step=100)
    
    st.divider()
    link_1 = st.text_input("URL 1")
    anchor_1 = st.text_input("Anchor 1")
    link_2 = st.text_input("URL 2 (Optioneel)")
    anchor_2 = st.text_input("Anchor 2")
    
    subject = st.text_area("Insteek", value="Waarom we vaker de bezem door ons leven halen.")
    
    start_btn = st.button("EXECUTE PRODUCTION", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Briefing onvolledig.")
    else:
        with st.status("🏗️ Agentic Loop in uitvoering...", expanded=True) as status:
            # FASE 1
            st.write("📐 **Architect** ontwerpt de intellectuele diepgang...")
            blueprint = call_ai(f"Onderwerp: {subject}", ARCHITECT_PROMPT.format(target=word_count_target))
            
            # FASE 2
            h2_sections = re.split(r'##', blueprint)[1:]
            full_raw_content = ""
            section_target = (word_count_target // 4) + 150 # Forceer volume
            
            for i, s in enumerate(h2_sections):
                st.write(f"🖋️ **Titan Writer** (Hoofdstuk {i+1}) bouwt het verhaal...")
                section_text = call_ai(
                    f"Sectie Blueprint: {s}\nLinks: {link_1} ({anchor_1}), {link_2} ({anchor_2})",
                    WRITER_PROMPT.format(section_target=section_target, client=client_name, link1=link_1),
                    temp=0.9 # Iets hoger voor maximale menselijke variatie
                )
                full_raw_content += f"\n\n## {section_text}"
                time.sleep(1)

            # FASE 3
            st.write("✨ **Assembler** polijst de cadans en flow...")
            final_article = call_ai(f"Smeed dit aaneen tot één essay:\n{full_raw_content}", ASSEMBLER_PROMPT, temp=0.7)
            
            # FASE 4
            st.write("🧐 **Gatekeeper** voert de finale audit uit...")
            score_raw = call_ai(
                f"Beoordeel op target {word_count_target}:\n\n{final_article}", 
                SCORER_PROMPT.format(target=word_count_target), 
                temp=0.1, 
                response_format={"type": "json_object"}
            )
            
            score_data = json.loads(score_raw)
            final_score = score_data.get("score", 0)
            
            if final_score >= 85:
                status.update(label=f"✅ Asset Goedgekeurd (Score: {final_score})", state="complete")
            else:
                status.update(label=f"❌ Asset Afgekeurd (Score: {final_score})", state="error")

        # --- OUTPUT ---
        tab1, tab2, tab3 = st.tabs(["💎 Final Asset", "📊 Audit Rapport", "🧬 Blueprint"])
        
        with tab1:
            if final_score >= 85:
                c_final = count_words(final_article)
                st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
                st.markdown(final_article)
                st.download_button("Download Asset", final_article, file_name="output.md")
            else:
                st.warning(f"Kwaliteit te laag ({final_score}). Zie Rapport.")
                st.error(score_data.get("reasoning"))
                st.info("Verbeterpunten: " + score_data.get("improvements"))
        
        with tab2:
            st.json(score_data)
            st.text_area("Rauwe Tekst", final_article, height=400)
            
        with tab3:
            st.markdown(blueprint)
