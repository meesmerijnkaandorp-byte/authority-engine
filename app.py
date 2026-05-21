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

# --- AGENT 1: THE ARCHITECT ---
ARCHITECT_PROMPT = """Jij bent de Lead Content Strategist. Maak een gedetailleerde 'Paragraph Map' voor een essay van {target} woorden.
EISEN:
- Verdeel het onderwerp in exact 4 grote H2-secties.
- Definieer per H2-sectie 4 specifieke, menselijke invalshoeken of scènes.
- De insteek moet lijken op kwaliteitsjournalistiek (bijv. NRC of Volkskrant Magazine).
- TAAL: Uitsluitend Nederlands.
"""

# --- AGENT 2: THE TITAN WRITER ---
WRITER_PROMPT = """Jij bent een freelance journalist. Je schrijft beeldend, scherp en wars van AI-clichés.

JOUW OPDRACHT:
Schrijf de volledige tekst voor de toegewezen H2-sectie.
EIS: Schrijf minimaal {section_target} woorden voor DEZE sectie.

STIJLREGELS:
- 'SHOW, DON'T TELL': Beschrijf situaties, geluiden en emoties.
- GEEN FLUFF: Gebruik geen woorden als 'uniek', 'oplossing', 'innovatief', 'cruciaal'.
- TAAL: Rijk, volwassen Nederlands. Geen constructies als 'de beginnings'.
- BRANDING: De klant ({client}) en links ({link1}) moeten organisch vloeien.
"""

# --- AGENT 3: THE ASSEMBLER ---
ASSEMBLER_PROMPT = """Jij bent een Meester-Redacteur. Smeed de hoofdstukken aaneen.
1. Maak vloeiende overgangen.
2. VERWIJDER NIETS uit de brontekst.
3. Voeg SEO-metadata toe aan de top.
4. Schrap AI-overgangswoorden (Kortom, Daarnaast).
"""

# --- AGENT 4: THE FINAL SCORER (Fixed for KeyError) ---
SCORER_PROMPT = """Jij bent een genadeloze Hoofdredacteur. Beoordeel de tekst op een schaal van 0-100.
CRITERIA:
- Woordental: Is het doel van {target} woorden gehaald?
- Vibe: Is de tekst menselijk of voelt het als AI?
- Taalgebruik: Zijn er kromme vertalingen of clichés?

STRICTE OUTPUT: Je MOET antwoorden in JSON-formaat. 
GEBRUIK EXACT DIT FORMAT:
{{
    "score": 88, 
    "reasoning": "Uitleg waarom", 
    "improvements": "Wat ontbreekt er?"
}}
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
        
    response = client.chat.create(**args) # Let op: sommig versies gebruiken client.chat.completions.create
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v4.5")
st.subheader("High-Fidelity Content Pipeline")

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
    
    subject = st.text_area("Insteek", value="De psychologie van de grote herinrichting.")
    start_btn = st.button("START PRODUCTIE", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Vul de verplichte velden in.")
    else:
        with st.status("🏗️ Productie-lijn draait...", expanded=True) as status:
            # FASE 1: ARCHITECT
            st.write("📐 Architect ontwerpt de diepgang...")
            blueprint = call_ai(f"Insteek: {subject}", ARCHITECT_PROMPT.format(target=word_count_target))
            
            # FASE 2: SEQUENTIAL WRITING
            h2_sections = re.split(r'##', blueprint)[1:]
            full_raw_content = ""
            section_target = (word_count_target // 4) + 100 
            
            for i, s in enumerate(h2_sections):
                st.write(f"🖋️ Writer produceert Hoofdstuk {i+1}...")
                section_text = call_ai(
                    f"Sectie: {s}\nLinks: {link_1} ({anchor_1})",
                    WRITER_PROMPT.format(section_target=section_target, client=client_name, link1=link_1),
                    temp=0.85
                )
                full_raw_content += f"\n\n## {section_text}"
                time.sleep(1)

            # FASE 3: ASSEMBLER
            st.write("✨ Assembler smeedt de narratieve lijm...")
            final_article = call_ai(f"Content: {full_raw_content}", ASSEMBLER_PROMPT, temp=0.7)
            
            # FASE 4: THE GATEKEEPER
            st.write("🧐 De Poortwachter controleert de eindkwaliteit...")
            # Hier ging het mis met de KeyError - nu opgelost met {{ }}
            score_raw = call_ai(
                f"Beoordeel op basis van {word_count_target} woorden:\n\n{final_article}", 
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

        # --- RESULTATEN ---
        tab1, tab2 = st.tabs(["💎 Final Asset", "📊 Audit Rapport"])
        
        with tab1:
            if final_score >= 85:
                c_final = count_words(final_article)
                st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
                st.markdown(final_article)
                st.download_button("Download Asset", final_article, file_name="export.md")
            else:
                st.warning(f"Tekst verborgen (Score: {final_score}). Zie Audit Rapport.")
                st.error(score_data.get("reasoning"))
        
        with tab2:
            st.json(score_data)
            st.text_area("Rauwe Tekst", final_article, height=300)
