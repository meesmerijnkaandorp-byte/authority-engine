import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v37.0 | Contextual Weaver", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

# --- HELPERS ---
def count_words(text):
    return len(text.split())

def clean_json_string(raw_string):
    clean = re.sub(r'```json\s*|```', '', raw_string)
    return clean.strip()

# --- SYSTEM PROMPTS (v37.0) ---

STRATEGIST_SYSTEM = """Jij bent een Hoofdredacteur. Je ontwerpt een artikel dat NAADLOOS past bij de publisher.
PUBLISHER CONTEXT: {publisher_info}
PRODUCT URL: {url}

TAAK:
1. Verzin een thema dat 100% past bij de publisher (bijv. 'De kunst van urenlang tafelen' of 'Gastvrijheid met een vleugje citroen').
2. Gebruik de 'Thematische Brug': Start bij de niche van de publisher (koken/recepten) en eindig bij het belang van goed zitten ({anchor}).
3. SCHEMA: {{ "title": "Kop", "sections": [ {{ "h2": "Kop", "focus": "inhoud", "link_logic": "hoe weven we de link hierin?" }} ] }}
"""

WRITER_SYSTEM = """Jij bent de auteur van de website: {publisher_info}. 
Schrijf in JOUW eigen stijl. Gebruik woorden die passen bij jouw niche (bijv. zuren, aroma's, bereidingstijd, textuur).
EIS: Geen droge opsommingen van materialen. Schrijf een verhalend essay.
VERBODEN: oase, cruciaal, essentieel, wereld van verschil, esthetiek."""

EDITOR_SYSTEM = """Jij bent de eindredacteur. Smeed het geheel aaneen.
TAAK:
1. De link [{anchor}]({url}) MOET midden in een zin staan die gaat over de ERVARING van de lezer op deze site.
2. Zorg dat de overgang van de niche (bijv. citroenen) naar het anker ({anchor}) niet aanvoelt als een advertentie, maar als een logisch advies voor de thuiskok/genieter.
3. Gebruik ## en ** voor scannability.

SCHEMA: {{ "title": "Kop", "meta": "Meta", "body": "Tekst met [ANCHOR_SPOT]" }}
"""

# --- AI WRAPPER ---
def call_ai(system, prompt, temp=0.7, json_mode=False):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=temp,
            response_format={"type": "json_object"} if json_mode else None
        )
        return response.choices[0].message.content
    except Exception as e: return f"ERROR: {str(e)}"

# --- UI ---
st.title("🛡️ Authority Engine v37.0")
st.caption("Contextual Weaver | Publishers-first AI Production")

with st.sidebar:
    st.header("📋 Master Briefing")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    
    st.divider()
    publisher_info = st.text_area("Publisher Niche", value="Culinaire website met eenvoudige recepten en de biologische citroen in de hoofdrol.")
    word_count_target = st.slider("Target", 600, 1500, 950)
    start_btn = st.button("WEAVE CONTENT", type="primary")

if start_btn:
    start_time = time.time()
    
    with st.status("🏗️ Thematische brug bouwen...", expanded=True) as status:
        
        # 1. STRATEGIST (Contextuele Koppeling)
        st.write("📐 Fase 1: Niche-analyse en brug-ontwerp...")
        strat_sys = STRATEGIST_SYSTEM.format(publisher_info=publisher_info, url=target_url, anchor=anchor_text)
        blueprint_raw = call_ai(strat_sys, "Ontwerp de rode draad.", json_mode=True)
        blueprint = json.loads(clean_json_string(blueprint_raw))

        # 2. WRITER (Niche-specifiek schrijven)
        st.write(f"🖋️ Fase 2: Schrijven vanuit de '{publisher_info}' gedachte...")
        full_draft = ""
        for section in blueprint["sections"]:
            write_sys = WRITER_SYSTEM.format(publisher_info=publisher_info, ban_list="oase, cruciaal")
            draft = call_ai(write_sys, f"H2: {section['h2']}\nFocus: {section['focus']}\nTarget: 250 woorden.")
            full_draft += f"\n\n## {section['h2']}\n{draft}"

        # 3. EDITOR (Chirurgische Link-integratie)
        st.write("✨ Fase 3: Redactie & Link-weving...")
        editor_sys = EDITOR_SYSTEM.format(anchor=anchor_text, url=target_url, publisher_context=publisher_info)
        editor_raw = call_ai(editor_sys, f"Smeed aaneen:\n{full_draft}", json_mode=True)
        final_data = json.loads(clean_json_string(editor_raw))

        # 4. PYTHON INJECTION
        body = final_data["body"]
        if "[ANCHOR_SPOT]" in body:
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        else:
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            body = pattern.sub(f"[{anchor_text}]({target_url})", body, count=1)
        
        final_data["body"] = body
        status.update(label="✅ Asset Weaved", state="complete")

    # --- OUTPUT ---
    st.header(final_data['title'])
    st.markdown(final_data['body'])
    st.download_button("Download Asset", final_data['body'], file_name="niche_asset.md")
