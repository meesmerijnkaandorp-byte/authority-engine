import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v7.0 | THE ENFORCER", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (Topic & Context Lock) ---
ARCHITECT_PROMPT = """Jij bent de Lead Strategist. Ontwerp een Paragraph Map voor een essay van {target} woorden.
ONDERWERP/URL: {url}
KLANT: {client}
ANKERTEKST: {anchor}

STRICTE EISEN:
1. FOCUS: Het artikel mag NIET gaan over de geschiedenis van het bedrijf. Het MOET gaan over het product in de URL ({url}) en de menselijke behoefte eromheen.
2. STRUCTUUR: Maak exact 5 grote H2-hoofdstukken.
3. DIEPGANG: Definieer per H2-sectie 5 specifieke, rauwe, alledaagse scènes of technische details.
4. ANKER: Bepaal in welke 2 hoofdstukken de ankertekst '{anchor}' verplicht op een cruciale plek moet staan.
5. TAAL: Nederlands. Geen marketing-clichés.
"""

# --- AGENT 2: THE TITAN WRITER (Anti-Cliché & Volume) ---
WRITER_PROMPT = """Jij bent een bekroonde journalist (denk aan Joris Luyendijk). Je schrijft feitelijk, scherp en met 'modder aan de schoenen'.

JOUW STIJL:
- GEEN METAFOREN: Verboden zijn: 'baken', 'feniks', 'horizon', 'geoliede machine', 'paradigmaverschuiving', 'in de wereld van', 'navigeren'.
- CONCREET: Gebruik zelfstandige naamwoorden. Praat over scharnieren, planken, de geur van spaanplaat, de chaos van rondslingerende kleding.
- LENGTE: Schrijf voor deze sectie minimaal {section_target} woorden. Gebruik GEEN herhalingen. Voeg nieuwe casuïstiek toe.

STRICT:
- Gebruik de ankertekst '{anchor}' op een natuurlijke, onzichtbare manier in de lopende tekst.
- Praat NOOIT over het proces van schrijven.
"""

# --- AGENT 3: THE ASSEMBLER (Flow & Guard) ---
ASSEMBLER_PROMPT = """Jij bent de Eindredacteur. Smeed 5 hoofdstukken aaneen tot één meesterwerk.
1. VERWIJDER NIETS. Behoud alle details en het volume.
2. SCAN & DELETE: Verwijder elke zin die klinkt als een samenvatting of een cliché-conclusie.
3. CHECK ANKER: Zorg dat de ankertekst '{anchor}' behouden blijft.
4. Metadata: Voeg Title, Meta en Slug toe (geen poëzie, gewoon harde SEO).
"""

# --- AGENT 4: THE GATEKEEPER (The Executioner) ---
SCORER_PROMPT = """Jij bent een cynische criticus. Beoordeel de tekst op target {target}.
KEUR AF (Score < 10) ALS:
1. De ankertekst '{anchor}' ontbreekt.
2. De tekst een geschiedenisles is over de klant in plaats van een artikel over het product.
3. Er woorden in staan zoals 'feniks', 'baken' of 'onstuimig'.
4. Het woordenaantal onder de {target} ligt.

JSON OUTPUT:
{{
    "score": 88,
    "reasoning": "Wees brutaal eerlijk.",
    "improvements": "Wat moet er concreet bij?"
}}
"""

# --- ENGINE ---
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

# --- UI ---
st.title("🛡️ Authority Engine v7.0")
st.subheader("The Enforcer: Zero-Cliché & Context-Locked Pipeline")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("Doel URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 2000, 1400, step=100)
    
    subject = st.text_area("Optionele Insteek", value="")
    start_btn = st.button("RUN ENFORCER PIPELINE", type="primary")

if start_btn:
    with st.status("🚀 Enforcer Mode Actief...", expanded=True) as status:
        # FASE 1
        st.write("📐 Architect vergrendelt context op URL...")
        blueprint = call_ai(f"Briefing: {subject}. URL: {target_url}", ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain, url=target_url, anchor=anchor_text), temp=0.7)
        
        # FASE 2
        h2_sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = (word_count_target // 5) + 100 
        
        for i, s in enumerate(h2_sections):
            st.write(f"🖋️ Titan Writer dwingt volume in Hoofdstuk {i+1}...")
            section_text = call_ai(
                f"Sectie: {s}\nAnkertekst VERPLICHT: {anchor_text}",
                WRITER_PROMPT.format(section_target=section_target, client=client_name, anchor=anchor_text),
                temp=0.85
            )
            full_raw_content += f"\n\n## {section_text}"
            time.sleep(1)

        # FASE 3
        st.write("✨ Assembler smeedt de narratieve ketting...")
        final_article = call_ai(f"Rauwe tekst:\n{full_raw_content}", ASSEMBLER_PROMPT.format(anchor=anchor_text), temp=0.7)
        
        # FASE 4
        st.write("🧐 Gatekeeper voert audit uit...")
        score_raw = call_ai(
            f"Tekst:\n\n{final_article}", 
            SCORER_PROMPT.format(target=word_count_target, anchor=anchor_text), 
            temp=0.1, 
            response_format={"type": "json_object"}
        )
        
        score_data = json.loads(score_raw)
        final_score = score_data.get("score", 0)
        
        if final_score >= 85:
            status.update(label=f"✅ Kwaliteit OK (Score: {final_score})", state="complete")
        else:
            status.update(label=f"❌ AFGEKEURD (Score: {final_score})", state="error")

    # --- RESULTAAT ---
    tab1, tab2, tab3 = st.tabs(["💎 Final Asset", "📊 Audit", "🧬 Blueprint"])
    with tab1:
        c_final = count_words(final_article)
        st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
        if final_score < 85:
            st.error(f"Score te laag: {final_score}. Analyseer rapport.")
        st.markdown(final_article)
        st.download_button("Download Asset", final_article, file_name="output.md")
    with tab2:
        st.json(score_data)
    with tab3:
        st.markdown(blueprint)
