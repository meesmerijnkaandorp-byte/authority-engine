import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v38.0 | Resilient Weaver", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

# --- ROBUUSTE HELPERS ---
def count_words(text):
    return len(text.split())

def clean_json_string(raw_string):
    """Vindt de eerste '{' en de laatste '}' om pure JSON te extraheren."""
    try:
        start = raw_string.find('{')
        end = raw_string.rfind('}') + 1
        if start == -1 or end == 0:
            return None
        json_str = raw_string[start:end]
        return json_str
    except:
        return None

# --- SYSTEM PROMPTS (v38.0) ---

STRATEGIST_SYSTEM = """Jij bent een Hoofdredacteur. Je ontwerpt een essay-structuur.
TAAK: Maak een brug tussen de PUBLISHER NICHE en het PRODUCT.
EIS: De tekst moet 100% aanvoelen als een artikel van de publisher.
LEVER UITSLUITEND JSON.

SCHEMA:
{{
  "title": "Kop van het artikel",
  "h2_1": "Titel eerste sectie",
  "focus_1": "Beschrijving inhoud",
  "h2_2": "Titel tweede sectie",
  "focus_2": "Beschrijving inhoud",
  "h2_3": "Titel derde sectie",
  "focus_3": "Beschrijving inhoud",
  "h2_4": "Titel vierde sectie",
  "focus_4": "Beschrijving inhoud"
}}"""

WRITER_SYSTEM = """Jij bent de auteur van: {publisher_info}. 
Schrijf in JOUW eigen unieke stijl. Gebruik jargon uit jouw niche.
EIS: GEEN bulletpoints. Schrijf uitsluitend LOPENDE ALINEA'S.
VERBODEN: oase, cruciaal, essentieel, wereld van verschil, harmonie, esthetiek."""

EDITOR_SYSTEM = """Jij bent de eindredacteur. Smeed de tekst aaneen tot een essay van {target} woorden.
TAAK:
1. Integreer de marker [ANCHOR_SPOT] naadloos in een zin die de lezer adviseert.
2. Zorg dat de overgang van {publisher_info} naar de ankertekst '{anchor}' logisch en nuchter is.
3. Gebruik ## voor koppen en ** voor nadruk.

LEVER UITSLUITEND JSON:
{{
  "title": "Definitieve Kop",
  "meta": "Meta omschrijving",
  "body": "Volledige tekst met ## en [ANCHOR_SPOT]"
}}"""

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
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v38.0")
st.caption("Resilient Weaver | Context-Aware & Crash-Proof")

with st.sidebar:
    st.header("📋 Master Briefing")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    
    st.divider()
    publisher_info = st.text_area("Publisher Niche", value="Culinaire website met eenvoudige recepten en de biologische citroen in de hoofdrol.")
    word_count_target = st.slider("Target Woorden", 600, 1500, 950)
    start_btn = st.button("WEAVE MASTER ASSET", type="primary")

if start_btn:
    start_time = time.time()
    
    with st.status("🏗️ Sovereign Weaver activeert...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Fase 1: Thematische brug ontwerpen...")
        strat_raw = call_ai(STRATEGIST_SYSTEM, f"URL: {target_url}. Publisher: {publisher_info}. Target: {word_count_target}", json_mode=True)
        clean_strat = clean_json_string(strat_raw)
        
        if not clean_strat:
            st.error("Kritieke fout: AI weigert JSON te leveren in de Strategist-fase.")
            st.code(strat_raw)
            st.stop()
            
        blueprint = json.loads(clean_strat)

        # 2. WRITER (Parallelle sectie-opbouw)
        st.write(f"🖋️ Fase 2: Schrijven in de stijl van '{publisher_info}'...")
        full_draft = ""
        # We halen de 4 secties uit de platte JSON
        for i in range(1, 5):
            h2_key = f"h2_{i}"
            focus_key = f"focus_{i}"
            st.write(f"  ✍️ Hoofdstuk {i}: {blueprint[h2_key]}")
            
            write_prompt = f"Onderwerp: {blueprint[h2_key]}. Focus: {blueprint[focus_key]}. Target: 250 woorden."
            draft = call_ai(WRITER_SYSTEM.format(publisher_info=publisher_info), write_prompt)
            full_draft += f"\n\n## {blueprint[h2_key]}\n{draft}"

        # 3. EDITOR
        st.write("✨ Fase 3: Eindredactie & Link-integratie...")
        editor_sys = EDITOR_SYSTEM.format(target=word_count_target, anchor=anchor_text, url=target_url, publisher_info=publisher_info)
        editor_raw = call_ai(editor_sys, f"Smeed dit aaneen tot een naadloos essay:\n{full_draft}", json_mode=True)
        clean_editor = clean_json_string(editor_raw)
        
        if not clean_editor:
            st.error("Kritieke fout: Editor leverde ongeldige JSON.")
            st.code(editor_raw)
            st.stop()
            
        final_data = json.loads(clean_editor)

        # 4. PYTHON INJECTION (De absolute garantie)
        body = final_data["body"]
        if "[ANCHOR_SPOT]" in body:
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        else:
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            body = pattern.sub(f"[{anchor_text}]({target_url})", body, count=1)
        
        final_data["body"] = body
        status.update(label="✅ Content Succesvol Geweven", state="complete")

    # --- OUTPUT ---
    st.header(final_data['title'])
    st.markdown(final_data['body'])
    
    with st.expander("Metadata & QA"):
        st.write(f"**Volume:** {count_words(final_data['body'])} woorden")
        st.write(f"**Meta Description:** {final_data.get('meta', 'Geen meta')}")
        st.write(f"**Link Check:** {'✅' if f'({target_url})' in final_data['body'] else '❌'}")

    st.download_button("Download Asset", final_data['body'], file_name="publisher_asset.md")
