import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v7.0 | THE ENFORCER", layout="wide")

# Beveiliging: OpenAI Key uit Streamlit Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: OpenAI API-sleutel niet gevonden in Secrets.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (De Strategische Blueprint) ---
ARCHITECT_PROMPT = """Jij bent de Lead Content Strategist. Jouw taak is het ontwerpen van een 'Paragraph Map' voor een diepgaand essay van {target} woorden.

JOUW OPDRACHT:
1. FOCUS: Het artikel mag NIET gaan over de geschiedenis van het bedrijf. Het MOET gaan over het specifieke product in de URL ({url}) en de menselijke behoeften/problemen die dit product oplost.
2. STRUCTUUR: Maak exact 5 grote H2-hoofdstukken.
3. DIEPGANG: Definieer per H2-sectie 5 specifieke, rauwe, alledaagse scènes of technische details (bijv. niet 'ruimtegebrek', maar 'het frustrerende geluid van kledinghangers die tegen elkaar vechten in een te volle kast').
4. ANKER: Bepaal in welke hoofdstukken de ankertekst '{anchor}' verplicht op een natuurlijke plek moet staan.
5. TAAL: Gebruik uitsluitend rijk, journalistiek Nederlands.
"""

# --- AGENT 2: THE TITAN WRITER (De Harde Journalist) ---
WRITER_PROMPT = """Jij bent een bekroonde onderzoeksjournalist (stijl: Joris Luyendijk/Wired). Je schrijft feitelijk, scherp en wars van marketing-clichés.

JOUW IDENTITEIT:
- Je haat 'content'. Je schrijft verhalen die mensen raken omdat ze de realiteit beschrijven.
- GEEN METAFOREN: Verboden zijn: 'baken', 'feniks', 'horizon', 'geoliede machine', 'paradigmaverschuiving', 'in de wereld van', 'navigeren'.
- CONCREET: Gebruik zelfstandige naamwoorden. Praat over scharnieren, planken, de geur van hout, de psychologie van orde.
- GEEN META-TAAL: Praat NOOIT over het schrijven zelf. Schrijf geen introducties zoals "In dit hoofdstuk bespreken we...". Begin direct met de observatie.

STRICTE OPDRACHT:
1. Schrijf de volledige tekst voor de toegewezen H2-sectie.
2. EIS: Schrijf minimaal {section_target} woorden voor DEZE sectie alleen. Gebruik GEEN herhalingen.
3. ANKER: Verwerk de ankertekst '{anchor}' op een onzichtbare, organische manier in de tekst.
4. KLANT: De klant ({client}) is een facilitator, geen held. Noem de klant alleen waar het logisch is.
"""

# --- AGENT 3: THE ASSEMBLER (De Technisch Redacteur) ---
ASSEMBLER_PROMPT = """Jij bent de Technisch Eindredacteur. Je krijgt 5 hoofdstukken.
JOUW OPDRACHT:
1. Smeed de hoofdstukken aaneen tot één vloeiend geheel.
2. VERWIJDER NIETS. Je bent hier om volume te bewaken. Voeg alleen overgangszinnen toe om de flow te verbeteren.
3. SCAN & DELETE: Verwijder elke zin die klinkt als een samenvatting, een cliché-conclusie of een meta-opmerking over de tekst.
4. ANKER: Zorg dat de ankertekst '{anchor}' exact behouden blijft.
5. SEO: Voeg bovenaan Title Tag, Meta Description en URL Slug toe (geen poëzie, gewoon harde conversiegerichte SEO).
"""

# --- AGENT 4: THE GATEKEEPER (De Onverbiddelijke Scorer) ---
SCORER_PROMPT = """Jij bent een genadeloze Hoofdredacteur. Beoordeel de tekst op een schaal van 0-100.
JOUW EISEN:
1. ANKERTEKST: Ontbreekt '{anchor}'? Score = 0.
2. TOPIC: Is dit een geschiedenisles over de klant in plaats van een artikel over het product in de URL? Score < 20.
3. LENGTE: Is de tekst korter dan {target} woorden? Score < 50.
4. CLICHÉS: Bevat de tekst woorden als 'feniks', 'baken', 'onstuimig' of 'ontdek'? Score < 40.

STRICTE JSON OUTPUT:
{{
    "score": 88,
    "reasoning": "Brutaal eerlijke analyse.",
    "improvements": "3 concrete actiepunten om de tekst menselijker en langer te maken."
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
        
    response = client.chat.completions.create(**args)
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v7.0")
st.subheader("The Enforcer: Industrial Content Production Line")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Naam Klant", value="VidaXL")
    target_url = st.text_input("Doel URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Doelplatform", value="dagelijksestandaard.nl")
    
    st.divider()
    word_count_target = st.slider("Target Woorden", 600, 2000, 1400, step=100)
    
    subject = st.text_area("Insteek (Optioneel)", value="De psychologie van opruimen en hoe de juiste kledingkast zorgt voor mentale rust.")
    
    start_btn = st.button("EXECUTE ENFORCER PIPELINE", type="primary")

if start_btn:
    if not client_name or not target_url or not anchor_text:
        st.error("Vul alle verplichte velden in.")
    else:
        with st.status("🏗️ Productielijn gestart (Enforcer Mode)...", expanded=True) as status:
            # FASE 1: ARCHITECT
            st.write("📐 Fase 1: Architectuur vergrendelen op URL...")
            blueprint = call_ai(
                f"Briefing: {subject}. URL: {target_url}", 
                ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain, url=target_url, anchor=anchor_text), 
                temp=0.7
            )
            
            # FASE 2: SEQUENTIAL PRODUCTION
            h2_sections = re.split(r'##', blueprint)[1:]
            full_raw_content = ""
            # We mikken per sectie op 20% van target + 150 woorden buffer
            section_target = (word_count_target // 5) + 150 
            
            for i, s in enumerate(h2_sections):
                st.write(f"🖋️ Fase 2.{i+1}: Writer dwingt volume in Hoofdstuk {i+1}...")
                section_text = call_ai(
                    f"Sectie-instructies: {s}\nAnkertekst VERPLICHT: {anchor_text}",
                    WRITER_PROMPT.format(section_target=section_target, client=client_name, anchor=anchor_text, link1=target_url),
                    temp=0.85
                )
                full_raw_content += f"\n\n## {section_text}"
                time.sleep(1)

            # FASE 3: ASSEMBLER
            st.write("✨ Fase 3: Assemblage (Zonder informatieverlies)...")
            final_article = call_ai(f"Rauwe tekst:\n{full_raw_content}", ASSEMBLER_PROMPT.format(anchor=anchor_text), temp=0.7)
            
            # FASE 4: GATEKEEPER
            st.write("🧐 Fase 4: Finale Audit & Scoring...")
            score_raw = call_ai(
                f"Eindproduct ter beoordeling:\n\n{final_article}", 
                SCORER_PROMPT.format(target=word_count_target, anchor=anchor_text), 
                temp=0.1, 
                response_format={"type": "json_object"}
            )
            
            score_data = json.loads(score_raw)
            final_score = score_data.get("score", 0)
            
            if final_score >= 85:
                status.update(label=f"✅ Kwaliteit Goedgekeurd (Score: {final_score})", state="complete")
            else:
                status.update(label=f"❌ Kwaliteit Afgekeurd (Score: {final_score})", state="error")

        # --- OUTPUT WEERGAVE ---
        tab1, tab2, tab3 = st.tabs(["💎 Final Asset", "📊 Audit Rapport", "🧬 Blueprint"])
        
        with tab1:
            c_final = count_words(final_article)
            st.metric("Gerealiseerd Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
            
            if final_score < 85:
                st.warning(f"De Gatekeeper heeft deze tekst afgekeurd ({final_score}/100). Verbeter de briefing of de insteek.")
            
            st.markdown(final_article)
            st.download_button("Download Markdown", final_article, file_name=f"{client_name}_article.md")
            
        with tab2:
            st.json(score_data)
            st.subheader("Rauwe tekst voor analyse:")
            st.text_area("Rauw", final_article, height=300)
            
        with tab3:
            st.markdown(blueprint)
