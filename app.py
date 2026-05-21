import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v6.0 | Industrial Grade", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt in Streamlit Secrets.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (De Strategische Blauwdruk) ---
ARCHITECT_PROMPT = """Jij bent de Lead Strategist bij een top-mediahuis. Jouw taak is het ontwerpen van een 'Paragraph Map' voor een diepgaand essay van {target} woorden.

JOUW OPDRACHT:
1. Verdeel het onderwerp in exact 4 grote H2-secties.
2. Definieer per H2-sectie 4 specifieke, feitelijke sub-onderwerpen of scènes.
3. Verbied abstracties; dwing de schrijver tot concrete details (bijv. niet 'service', maar 'de monteur die om 07:00 op de stoep staat').
4. GEEN ENGELS. Gebruik uitsluitend rijk Nederlands.
5. Focus 100% op de materie van de klant ({client}) en de zoekintentie van het platform ({platform}).
"""

# --- AGENT 2: THE TITAN WRITER (De Harde Journalist) ---
WRITER_PROMPT = """Jij bent een bekroonde onderzoeksjournalist. Je haat 'content' en schrijft uitsluitend 'meesterwerken'.

JOUW IDENTITEIT & STIJL:
- Je bent een meester in 'Show, Don't Tell'. Beschrijf de realiteit: de geur, het gewicht, de frustratie, de oplossing.
- Je taalgebruik is 100% Nederlands. Vermijd Engelse constructies of letterlijke vertalingen (NOOIT 'de beginnings', 'aan de slag gaan', of 'het draait allemaal om').
- Je varieert je zinslengte: korte, mokerslag-zinnen afgewisseld met diepe, intellectuele observaties.
- Je gebruikt 'low-frequency' woorden: woorden die diepgang verraden (bijv. 'steevast', 'ontegenzeggelijk', 'ambiguïteit', 'saillant').

STRICTE OPDRACHT:
1. Schrijf de volledige tekst voor de toegewezen H2-sectie.
2. EIS: Schrijf minimaal {section_target} woorden. Gebruik geen herhalingen, maar voeg nieuwe feiten en perspectieven toe.
3. SCHRIJF NOOIT OVER HET SCHRIJVEN. Geen meta-teksten over 'verbinding' of 'ritme'. Praat alleen over het onderwerp.
4. BRANDING: Verwerk de klant ({client}) en de link ({link1}) als essentieel onderdeel van het betoog.
"""

# --- AGENT 3: THE ASSEMBLER (De Technisch Eindredacteur) ---
ASSEMBLER_PROMPT = """Jij bent een Technisch Eindredacteur. Je krijgt 4 hoofdstukken van een groot essay.
JOUW OPDRACHT:
1. Smeed de hoofdstukken aaneen met natuurlijke overgangszinnen.
2. VERWIJDER NIETS. Je bent hier om volume te bewaken en flow toe te voegen.
3. Verwijder elke zin die praat over 'de kunst van het schrijven' of 'deze tekst'.
4. Schrap AI-clichés: 'kortom', 'daarnaast', 'in deze wereld', 'bovendien'.
5. Voeg bovenaan SEO-metadata toe: Title Tag (max 60), Meta Description (max 155), URL Slug.
"""

# --- AGENT 4: THE GATEKEEPER (De Onverbiddelijke Scorer) ---
SCORER_PROMPT = """Jij bent een algoritme dat content beoordeelt op menselijkheid en autoriteit.
CRITERIA:
1. TOPIC FOCUS: Gaat de tekst over de klant en het onderwerp? (100% vereist).
2. LENGTE: Wordt de {target} woorden gehaald?
3. TAAL: Is het rijk Nederlands zonder Engelse invloeden?
4. GEEN META: Praat de tekst over zichzelf of over 'schrijven'? (Indien ja: Score = 0).

STRICTE OUTPUT IN JSON:
{{
    "score": 88,
    "reasoning": "Kritische analyse van de tekst.",
    "improvements": "3 harde actiepunten."
}}
"""

# --- AI ENGINE ---
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
st.title("🛡️ Authority Engine v6.0")
st.subheader("Industrial Content Production: Zero-Hallucination Pipeline")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 2000, 900, step=100)
    
    st.divider()
    link_1 = st.text_input("URL 1")
    anchor_1 = st.text_input("Anchor 1")
    link_2 = st.text_input("URL 2 (Optioneel)")
    anchor_2 = st.text_input("Anchor 2")
    
    subject = st.text_area("Insteek", value="Waarom een goed georganiseerd huis essentieel is voor je mentale rust.")
    start_btn = st.button("START PRODUCTIE", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Briefing onvolledig. Controleer Klant, Platform en URL.")
    else:
        with st.status("🏗️ Industrial Pipeline actief...", expanded=True) as status:
            # FASE 1: ARCHITECT
            st.write("📐 Fase 1: Architectuur ontwerpen (Paragraph Map)...")
            blueprint = call_ai(
                f"Onderwerp: {subject}", 
                ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain), 
                temp=0.7
            )
            
            # FASE 2: SEQUENTIAL PRODUCTION
            h2_sections = re.split(r'##', blueprint)[1:]
            full_raw_content = ""
            # We mikken op 25% van target + 125 woorden buffer om luiheid te compenseren
            section_target = (word_count_target // 4) + 125 
            
            for i, s in enumerate(h2_sections):
                st.write(f"🖋️ Fase 2.{i+1}: Writer produceert Hoofdstuk {i+1} ({section_target}+ woorden)...")
                section_text = call_ai(
                    f"Sectie-instructies: {s}\nAnkertekst: {anchor_1}\nURL: {link_1}\nLink 2: {link_2} ({anchor_2})",
                    WRITER_PROMPT.format(section_target=section_target, client=client_name, link1=link_1),
                    temp=0.85
                )
                full_raw_content += f"\n\n## {section_text}"
                time.sleep(1)

            # FASE 3: ASSEMBLER
            st.write("✨ Fase 3: Assemblage & Narratieve Flow...")
            final_article = call_ai(f"Smeed dit aaneen tot één essay over {subject} voor {target_domain}. Rauwe tekst:\n{full_raw_content}", ASSEMBLER_PROMPT, temp=0.7)
            
            # FASE 4: GATEKEEPER
            st.write("🧐 Fase 4: Kwaliteitscontrole (Score-Gate)...")
            score_raw = call_ai(
                f"Beoordeel deze tekst op basis van doel {word_count_target}:\n\n{final_article}", 
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

        # --- OUTPUT ---
        tab1, tab2, tab3 = st.tabs(["💎 Final Asset", "📊 Audit Rapport", "🧬 Blueprint"])
        
        with tab1:
            if final_score >= 85:
                c_final = count_words(final_article)
                st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
                st.markdown(final_article)
                st.download_button("Download Asset", final_article, file_name="export.md")
            else:
                st.warning(f"Output geblokkeerd. Score: {final_score}/100.")
                st.error(f"REDE: {score_data.get('reasoning')}")
                st.info(f"VERBETERINGEN: {score_data.get('improvements')}")
                st.subheader("Rauwe tekst voor analyse:")
                st.text_area("Ruw", final_article, height=300)
        
        with tab2:
            st.json(score_data)
        
        with tab3:
            st.markdown(blueprint)
