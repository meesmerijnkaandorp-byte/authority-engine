import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v4.5 | The Gatekeeper", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt in Streamlit Secrets.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (De Bouwtekening) ---
ARCHITECT_PROMPT = """Jij bent de Lead Content Strategist. Maak een gedetailleerde 'Paragraph Map' voor een essay van {target} woorden.
EISEN:
- Verdeel het onderwerp in exact 4 grote H2-secties.
- Definieer per H2-sectie 4 specifieke, menselijke invalshoeken of scènes (geen abstracte marketingtermen).
- De insteek moet lijken op kwaliteitsjournalistiek (bijv. NRC of Volkskrant Magazine).
- TAAL: Uitsluitend Nederlands.
"""

# --- AGENT 2: THE TITAN WRITER (Sectie-specialist) ---
WRITER_PROMPT = """Jij bent een freelance journalist voor bladen als Linda.man. Je schrijft beeldend, scherp en wars van AI-clichés.

JOUW OPDRACHT:
Schrijf de volledige tekst voor de toegewezen H2-sectie.
EIS: Schrijf minimaal {section_target} woorden voor DEZE sectie.

STIJLREGELS:
- 'SHOW, DON'T TELL': Beschrijf situaties, geluiden, texturen en emoties.
- GEEN FLUFF: Gebruik geen woorden als 'uniek', 'oplossing', 'innovatief', 'cruciaal'.
- GEEN SAMENVATTINGEN: Elke alinea moet dieper de materie in duiken.
- TAAL: Rijk, volwassen Nederlands. Geen constructies als 'de beginnings' of 'aan de slag gaan'.
- BRANDING: De klant ({client}) en links ({link1}) moeten organisch vloeien in de tekst.
"""

# --- AGENT 3: THE ASSEMBLER (De Lijm) ---
ASSEMBLER_PROMPT = """Jij bent een Meester-Redacteur. Smeed de 4 hoofdstukken aaneen.
TAAK:
1. Maak vloeiende overgangen tussen alinea's en hoofdstukken.
2. VERWIJDER NIETS. Je mag alleen tekst toevoegen om de flow te verbeteren.
3. Voeg SEO-metadata toe (Title Tag, Meta Description, URL Slug) aan de top.
4. Schrap AI-overgangswoorden (Kortom, Daarnaast, Bovendien).
"""

# --- AGENT 4: THE FINAL SCORER (De Poortwachter) ---
SCORER_PROMPT = """Jij bent een genadeloze Hoofdredacteur. Beoordeel de tekst op een schaal van 0-100.
CRITERIA:
- Woordental: Is het doel van {target} woorden gehaald? (Zwaar meewegen)
- Vibe: Is de tekst menselijk of voelt het als AI?
- Taalgebruik: Zijn er kromme vertalingen of clichés?
- E-E-A-T: Straalt de tekst autoriteit uit?

STRICTE OUTPUT: Je MOET antwoorden in JSON-formaat:
{"score": 88, "reasoning": "Uitleg waarom", "improvements": "Wat ontbreekt er?"}
"""

# --- AI CALL FUNCTIE ---
def call_ai(prompt, system_instruction, temp=0.8, response_format=None):
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
st.title("🛡️ Authority Engine v4.5")
st.subheader("High-Fidelity Content Pipeline met Kwaliteits-Gate")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="Avis")
    target_domain = st.text_input("Platform", value="Lifestyle Magazine")
    word_count_target = st.slider("Target Woorden", 600, 1500, 900, step=100)
    
    st.divider()
    link_1 = st.text_input("URL 1")
    anchor_1 = st.text_input("Anchor 1")
    link_2 = st.text_input("URL 2 (Optioneel)")
    anchor_2 = st.text_input("Anchor 2")
    
    subject = st.text_area("Insteek", value="De psychologie van de grote herinrichting: waarom we vaker de bezem door ons leven halen.")
    
    start_btn = st.button("START PRODUCTIE", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Vul de verplichte velden in.")
    else:
        with st.status("🏗️ Productie-lijn draait...", expanded=True) as status:
            # FASE 1: ARCHITECT
            st.write("📐 Architect ontwerpt de diepgang...")
            blueprint = call_ai(f"Onderwerp: {subject}", ARCHITECT_PROMPT.format(target=word_count_target, subject=subject, client=client_name, platform=target_domain), temp=0.7)
            
            # FASE 2: SEQUENTIAL WRITING
            h2_sections = re.split(r'##', blueprint)[1:]
            full_raw_content = ""
            section_target = (word_count_target // 4) + 100 
            
            for i, s in enumerate(h2_sections):
                st.write(f"🖋️ Writer produceert Hoofdstuk {i+1}...")
                section_text = call_ai(
                    f"Sectie Blueprint: {s}\nLinks: {link_1} ({anchor_1}), {link_2} ({anchor_2})",
                    WRITER_PROMPT.format(section_target=section_target, client=client_name, link1=link_1),
                    temp=0.85
                )
                full_raw_content += f"\n\n## {section_text}"
                time.sleep(1)

            # FASE 3: ASSEMBLER
            st.write("✨ Assembler smeedt de narratieve lijm...")
            final_article = call_ai(f"Content: {full_raw_content}", ASSEMBLER_PROMPT, temp=0.7)
            
            # FASE 4: THE GATEKEEPER (Hidden Scoring)
            st.write("🧐 De Poortwachter controleert de eindkwaliteit...")
            score_raw = call_ai(
                f"Beoordeel deze tekst op basis van het doel van {word_count_target} woorden:\n\n{final_article}", 
                SCORER_PROMPT.format(target=word_count_target), 
                temp=0.1, 
                response_format={"type": "json_object"}
            )
            
            score_data = json.loads(score_raw)
            final_score = score_data.get("score", 0)
            
            if final_score >= 85:
                status.update(label=f"✅ Kwaliteit Goedgekeurd (Score: {final_score})", state="complete")
            else:
                status.update(label=f"❌ Kwaliteit Onvoldoende (Score: {final_score})", state="error")

        # --- RESULTATEN WEERGAVE ---
        tab1, tab2 = st.tabs(["💎 Final Asset", "📊 Audit Rapport"])
        
        with tab1:
            if final_score >= 85:
                c_final = count_words(final_article)
                st.metric("Gerealiseerd Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
                st.markdown(final_article)
                st.download_button("Download Asset", final_article, file_name=f"{client_name}_export.md")
            else:
                st.warning(f"De tekst is verborgen omdat de kwaliteitsscore ({final_score}) onder de limiet van 85 ligt.")
                st.error("REDEN VAN AFKEURING:")
                st.write(score_data.get("reasoning"))
                st.info("GEWENSTE VERBETERINGEN:")
                st.write(score_data.get("improvements"))
        
        with tab2:
            st.json(score_data)
            if final_score < 85:
                st.subheader("Rauwe Tekst (ter analyse):")
                st.text_area("Bekijk hier de afgekeurde tekst", final_article, height=300)
