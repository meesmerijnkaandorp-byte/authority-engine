import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v16.0 | The Ghostwriter Protocol", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (The Scene Planner) ---
# Deze agent plant geen onderwerpen, maar 'momenten'.
ARCHITECT_PROMPT = """Jij bent een bekroonde literair redacteur. Plan een essay voor {target} woorden over de producten op {url}.

JOUW OPDRACHT:
1. VERBODEN: Plan geen informatie. Plan ERVARINGEN.
2. SCÈNE-MAPPING: Maak 4 hoofdstukken (H2) gebaseerd op specifieke situaties:
   - De ochtendstress (het gevecht met de hanger).
   - De materiële realiteit (het gewicht van hout, de scherpte van staal).
   - De psychologie van bezit (waarom we bewaren wat we niet dragen).
   - De bevrijding (de lege vloer, de geordende plank).
3. GEEN MARKETING: Als ik één woord over 'klantvoordelen' zie, faal je.
"""

# --- AGENT 2: THE TITAN WRITER (The Misanthrope) ---
# We maken hem een tikkeltje cynisch om de AI-beleefdheid te breken.
WRITER_PROMPT = """Jij bent een scherpe, nuchtere columnist voor een kwaliteitskrant. Je haat AI-slop en je haat 'uitleggen'.

JOUW OPDRACHT:
Schrijf hoofdstuk {n}. 
- STIJL: Rauw, observerend, subjectief. Gebruik de 'Show, Don't Tell' methode van de Avis-tekst (zaterdagmorgen-energie, specifieke details).
- VERBODEN WOORDEN (100% BAN): essentieel, cruciaal, wereld van verschil, harmonie, oase, beleving, uniek, ontdek, perfect, optimaal, daarnaast, kortom.
- EIS: Gebruik per alinea minimaal één fysiek detail (een geur, een geluid, een textuur).
- ZINSBOUW: Varieer extreem. Eén zin van drie woorden. Daarna een diepe, ronkende observatie.

{link_instruction}
"""

# --- AGENT 3: THE ASSEMBLER (The Soul-Crusher) ---
# Deze agent verwijdert elke zin die ruikt naar een robot.
ASSEMBLER_PROMPT = """Jij bent de meest gevreesde eindredacteur van Nederland. 
1. SCAN OP ROBOTS: Verwijder elke zin die klinkt alsof een machine hem heeft geschreven om 'behulpzaam' te zijn.
2. LINK-CHECK: Zorg dat de link [{anchor}]({url}) ergens midden in de tekst staat, NIET in een call-to-action aan het einde.
3. FLOW: Smeed de teksten aaneen tot een vloeiend essay van {target} woorden.
4. GEEN CONCLUSIE: Een menselijk essay eindigt met een nagedachte, niet met een samenvatting.
"""

# --- AGENT 4: THE GATEKEEPER (The Turing Tester) ---
SCORER_PROMPT = """Jij bent een AI-detector die getraind is op het haten van genericiteit.
BEPALING SCORE (0 = Menselijk, 100 = Robot):
- Punten erbij voor: 'Het is belangrijk om', 'Daarnaast', 'Cruciaal', 'Essentieel', 'Harmonie'.
- Punten erbij voor: Een nette structuur waarbij elke alinea even lang is.
- Punten eraf voor: Rauwe observaties, sarcasme, specifieke objecten (inbussleutels, stof).

STRICTE JSON OUTPUT:
{{
    "ai_score": 0,
    "reasoning": "Waarom voelt dit nog als een brochure?",
    "forbidden_words_found": []
}}
"""

# --- AI ENGINE ---
def call_ai(prompt, system_instruction, temp=0.9):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v16.0")
st.subheader("The Ghostwriter Protocol: Breaking the AI-Gravity")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Anker", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target", 600, 1500, 900, step=50)
    
    start_btn = st.button("RUN GHOSTWRITER", type="primary")

if start_btn:
    with st.status("🏗️ Realiteit aan het vangen...", expanded=True) as status:
        # FASE 1
        st.write("📐 Architect plant scènes...")
        blueprint = call_ai(f"Scenario voor {target_url}", ARCHITECT_PROMPT.format(target=word_count_target, url=target_url))
        
        # FASE 2
        h2_sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int(word_count_target // 4)
        
        for i, s in enumerate(h2_sections):
            # Link-injectie (verstopt)
            l_inst = f"VERSTOP de link [{anchor_text}]({target_url}) in een zin. GEEN promo-taal." if i == 1 else "GEBRUIK GEEN LINKS."
            
            st.write(f"  🖋️ Ghostwriter (Sectie {i+1})...")
            section_text = call_ai(
                f"Sectie: {s}",
                WRITER_PROMPT.format(n=i+1, section_target=section_target, client=client_name, link_instruction=l_inst),
            )
            full_raw_content += f"\n\n## {section_text}"

        # FASE 3
        st.write("  ✨ Assemblage & Soul-Injection...")
        final_article = call_ai(f"Smeed aaneen tot {word_count_target} woorden. Verwijder robot-taal:\n{full_raw_content}", 
                                ASSEMBLER_PROMPT.format(target=word_count_target, url=target_url, anchor=anchor_text), temp=0.8)
        
        # FASE 4
        st.write("  🧐 Turing Test...")
        score_raw = call_ai(f"Audit:\n\n{final_article}", SCORER_PROMPT.format(target=word_count_target, anchor=anchor_text, url=target_url), temp=0.1)
        
        try:
            score_json = re.search(r'\{.*\}', score_raw, re.DOTALL).group()
            score_data = json.loads(score_json)
        except:
            score_data = {"ai_score": 50, "reasoning": "Audit failed"}
        
        final_score = score_data.get("ai_score", 100)
        
        if final_score < 30: # Lage score is hier GOED
            status.update(label=f"✅ Menselijke Kwaliteit (AI-Score: {final_score})", state="complete")
        else:
            status.update(label=f"⚠️ AI-Fingerprint te hoog ({final_score})", state="error")

    # --- OUTPUT ---
    tab1, tab2 = st.tabs(["📄 Final Asset", "📊 Audit Log"])
    with tab1:
        st.metric("Gerealiseerd Volume", f"{count_words(final_article)} woorden")
        st.markdown(final_article)
        st.download_button("Download", final_article, file_name="ghostwriter_export.md")
    with tab2:
        st.json(score_data)
        st.text_area("Blueprint", blueprint)
