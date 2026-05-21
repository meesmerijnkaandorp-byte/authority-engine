import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v39.0 | Polyglot Architect", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

# --- ROBUUSTE HELPERS ---
def count_words(text):
    return len(text.split())

def clean_json_string(raw_string):
    try:
        start = raw_string.find('{')
        end = raw_string.rfind('}') + 1
        return raw_string[start:end] if start != -1 else None
    except:
        return None

# --- SYSTEM PROMPTS (v39.0) ---

STRATEGIST_SYSTEM = """Jij bent een Hoofdredacteur. Ontwerp een essay-structuur die de brug slaat.
PUBLISHER: {publisher_info}
PRODUCT: {anchor}

TAAK:
1. Start 100% in de wereld van de publisher (bijv. recepten, sfeer, cultuur).
2. Sla in de laatste sectie de brug naar de fysieke omgeving (het product).
3. LEVER UITSLUITEND JSON.
{{
  "title": "Creatieve kop",
  "sections": [ {{ "h2": "Kop", "focus": "Inhoudelijke focus" }} ]
}}"""

WRITER_SYSTEM = """Jij bent de auteur van {publisher_info}. Schrijf verhalend en met passie voor je niche.
GEBRUIK GEEN BULLETPOINTS. Schrijf uitsluitend in rijke, lopende alinea's.
GEBRUIK MARKDOWN: Gebruik **vetgedrukte tekst** voor accenten.
VERBODEN: oase, cruciaal, essentieel, wereld van verschil, esthetiek, harmonie."""

EDITOR_SYSTEM = """Jij bent de eindredacteur. Smeed alles aaneen tot een vloeiend essay van {target} woorden.

LINK-STRATEGIE ({mode}):
Ankertekst: '{anchor}'
- Bij 'Exact Match': Gebruik de term letterlijk. Zorg voor een correcte zin, bijvoorbeeld: "Wie overweegt een [ANCHOR_SPOT] te realiseren..." of "Het proces van een [ANCHOR_SPOT] vraagt om...".
- Bij 'Natuurlijk': Verbuig de term voor maximale leesbaarheid (bijv. "het kopen van een nieuwe stoel").

TAAK:
1. Gebruik ## voor koppen en voeg witregels toe.
2. De link [ANCHOR_SPOT] moet logisch volgen uit de tekst van de publisher: {publisher_info}.
3. LEVER UITSLUITEND JSON:
{{
  "title": "Titel", "meta": "Meta", "body": "Tekst met ## en [ANCHOR_SPOT]"
}}"""

# --- AI WRAPPER ---
def call_ai(system, prompt, temp=0.7, json_mode=False):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=temp,
        response_format={"type": "json_object"} if json_mode else None
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🛡️ Authority Engine v39.0")
st.caption("The Polyglot Architect | Linguistic Integrity & Bridge Logic")

with st.sidebar:
    st.header("📋 Master Briefing")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    anchor_mode = st.radio("Link Modus", ["Exact Match", "Natuurlijk/Vloeiend"])
    
    st.divider()
    publisher_info = st.text_area("Publisher Niche", value="Culinaire website met eenvoudige recepten en de biologische citroen in de hoofdrol.")
    word_count_target = st.slider("Target", 600, 1500, 950)
    start_btn = st.button("PRODUCEER MASTER ASSET", type="primary")

if start_btn:
    start_time = time.time()
    
    with st.status("🏗️ Sovereign Pipeline v39.0...", expanded=True) as status:
        
        # 1. STRATEGIST
        strat_sys = STRATEGIST_SYSTEM.format(publisher_info=publisher_info, anchor=anchor_text, url=target_url)
        blueprint = json.loads(clean_json_string(call_ai(strat_sys, "Ontwerp de brug.", json_mode=True)))

        # 2. WRITER
        full_draft = ""
        for section in blueprint["sections"]:
            write_sys = WRITER_SYSTEM.format(publisher_info=publisher_info)
            draft = call_ai(write_sys, f"Schrijf over: {section['h2']}. Focus: {section['focus']}. Target: 250 woorden.")
            full_draft += f"\n\n## {section['h2']}\n{draft}"

        # 3. EDITOR
        editor_sys = EDITOR_SYSTEM.format(target=word_count_target, anchor=anchor_text, mode=anchor_mode, publisher_info=publisher_info)
        final_json = json.loads(clean_json_string(call_ai(editor_sys, f"Smeed aaneen:\n{full_draft}", json_mode=True)))

        # 4. PYTHON INJECTION
        body = final_json["body"]
        if "[ANCHOR_SPOT]" in body:
            # Bij Natuurlijk laten we de AI de verbuiging al doen en vervangen we alleen de marker.
            # Bij Exact dwingen we de string erin.
            replacement = anchor_text if anchor_mode == "Exact Match" else anchor_text # AI doet de rest
            body = body.replace("[ANCHOR_SPOT]", f"[{replacement}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        
        final_json["body"] = body
        status.update(label="✅ Content Voltooid", state="complete")

    # --- OUTPUT ---
    st.header(final_json['title'])
    st.markdown(final_json['body'])
    
    with st.expander("Metadata & Instellingen"):
        st.write(f"**Anker-Modus:** {anchor_mode}")
        st.write(f"**Meta:** {final_json.get('meta')}")
        st.write(f"**Woorden:** {count_words(final_json['body'])}")

    st.download_button("Download Asset", final_json['body'], file_name="master_asset.md")
