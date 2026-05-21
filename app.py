import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v10.0 | Anti-Slop Edition", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt in Secrets.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (Nuchtere Planning) ---
ARCHITECT_PROMPT = """Jij bent een cynische Hoofdredacteur. Ontwerp een Paragraph Map voor {target} woorden.
ONDERWERP: {url}
KLANT: {client}
PLATFORM: {platform}

EISEN:
1. GEEN BULLSHIT: Schrijf niet over 'oases' of 'stijl'. Schrijf over de praktische realiteit: ruimtegebrek, montage, prijs, en duurzaamheid van {client}.
2. STRUCTUUR: 4 hoofdstukken (H2).
3. FOCUS: Gebruik technische details van de URL ({url}). Praat over materialen, afmetingen en de frustratie van rondslingerende troep.
4. TAAL: Nuchter Nederlands.
"""

# --- AGENT 2: THE TITAN WRITER (De Nuchtere Journalist) ---
WRITER_PROMPT = """Jij bent een nuchtere consumentenjournalist. Je schrijft voor mensen die een hekel hebben aan marketing-gezwets.

JOUW STIJL:
- ZWARTE LIJST (VERBODEN): 'oase', 'harmonieus', 'samenspel', 'ontdekkingsreis', 'beleving', 'esthetiek', 'minimalistisch', 'glamour', 'balans', 'duurzaamheid' (zonder bewijs).
- SCHRIJFSTIJL: Direct, feitelijk, observerend. Gebruik korte zinnen.
- SHOW, DON'T TELL: Schrijf over spaanplaat, schroeven, het gewicht van een jas, en de ruimte onder een bed.
- TAAL: Volwassen Nederlands. Geen 'AI-clichés' of Engelse zinsbouw.

{link_instruction}
"""

# --- AGENT 3: THE ASSEMBLER (De Schaar) ---
ASSEMBLER_PROMPT = """Jij bent een strenge Eindredacteur. Je krijgt 4 secties tekst.
JOUW OPDRACHT:
1. SINGLE LINK POLICY: Er mag in het HELE artikel slechts ÉÉN hyperlink staan naar {url}. Verwijder alle andere hyperlinks onmiddellijk en maak er platte tekst van.
2. SCHRAPPEN: Verwijder elke zin die klinkt als 'marketing-blabla' of 'AI-vulling'.
3. VOLUME: Smeed de tekst aaneen tot ongeveer {target} woorden.
4. METADATA: Title (feitelijk), Meta (direct), Slug.
"""

# --- AGENT 4: THE GATEKEEPER (De 'Slop' Detector) ---
SCORER_PROMPT = """Jij bent een AI-detectie specialist en taal-snob.
SCORE < 10 ALS:
- De woorden 'oase', 'harmonieus', 'samenspel' of 'beleving' voorkomen.
- Er meer dan één hyperlink in de tekst staat.
- De tekst klinkt als een verkoopbrochure in plaats van een journalistiek stuk.
- De ankertekst '{anchor}' niet exact één keer gelinkt is.

JSON OUTPUT:
{{
    "score": 0,
    "reasoning": "Wees genadeloos over AI-clichés.",
    "slop_count": "Aantal gevonden verboden woorden"
}}
"""

# --- ENGINE ---
def call_ai(prompt, system_instruction, temp=0.75, response_format=None):
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
st.title("🛡️ Authority Engine v10.0")
st.subheader("Anti-Slop Content Pipeline: Journalistieke Precisie")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 1500, 900, step=50)
    
    start_btn = st.button("GENEREER ZONDER SLOP", type="primary")

if start_btn:
    with st.status("🏗️ Pijplijn gesaneerd. Productie start...", expanded=True) as status:
        # FASE 1
        st.write("📐 Architect maakt nuchter plan...")
        blueprint = call_ai(f"URL: {target_url}. Klant: {client_name}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain, url=target_url))
        
        # FASE 2
        h2_sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int((word_count_target * 1.1) // 4)
        
        for i, s in enumerate(h2_sections):
            # HARD LINK CONTROL
            if i == 0:
                l_inst = f"VERPLICHTE LINK: Verwerk exact één keer de link [{anchor_text}]({target_url}) in de tekst."
            else:
                l_inst = "GEBRUIK GEEN HYPERLINKS. Schrijf alleen platte tekst."

            st.write(f"🖋️ Writer produceert Sectie {i+1}...")
            section_text = call_ai(
                f"Sectie: {s}",
                WRITER_PROMPT.format(section_target=section_target, client=client_name, link_instruction=l_inst),
                temp=0.8
            )
            full_raw_content += f"\n\n## {section_text}"
            time.sleep(0.5)

        # FASE 3
        st.write("✨ Assembler snijdt de fluff weg...")
        final_article = call_ai(f"Smeed dit aaneen tot {word_count_target} woorden. URL: {target_url}:\n{full_raw_content}", 
                                ASSEMBLER_PROMPT.format(target=word_count_target, url=target_url), temp=0.5)
        
        # FASE 4
        st.write("🧐 Gatekeeper controleert op AI-slop...")
        score_raw = call_ai(
            f"Tekst:\n\n{final_article}", 
            SCORER_PROMPT.format(target=word_count_target, anchor=anchor_text), 
            temp=0.1, 
            response_format={"type": "json_object"}
        )
        
        score_data = json.loads(score_raw)
        final_score = score_data.get("score", 0)
        
        if final_score >= 85:
            status.update(label=f"✅ Asset Goedgekeurd (Score: {final_score})", state="complete")
        else:
            status.update(label=f"❌ AFGEKEURD (Score: {final_score})", state="error")

    # OUTPUT
    tab1, tab2 = st.tabs(["💎 Asset", "📊 Audit"])
    with tab1:
        c_final = count_words(final_article)
        st.metric("Gerealiseerd Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
        if final_score < 85:
            st.error(f"Systeem blokkade: Tekst bevat te veel AI-kenmerken (Score: {final_score})")
            st.write(score_data.get("reasoning"))
        st.markdown(final_article)
    with tab2:
        st.json(score_data)
