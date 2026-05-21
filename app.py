import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v34.1 | Narrative Enforcer", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API-sleutel ontbreekt in Secrets.")

# --- HELPERS ---
def count_words(text):
    return len(text.split())

def clean_json_string(raw_string):
    clean = re.sub(r'```json\s*|```', '', raw_string)
    return clean.strip()

# --- DE GOUDEN STANDAARD ---
GOLDEN_EXAMPLE = """
"Je huis fungeert als tegenwicht voor de drukte buiten. Een opgeruimde omgeving helpt om je hoofd leeg te maken. Het gaat om het gevoel dat de ruimte je ondersteunt in plaats van afleidt."
"""

# --- SYSTEM PROMPTS (v34.1) ---

ANALYZER_SYSTEM = "Jij bent een Topic Auditor. Geef UITSLUITEND het fysieke hoofdonderwerp in 3 woorden."

STRATEGIST_SYSTEM = """Jij bent een Content Architect. Lever een JSON blueprint.
STIJL: Nuchter, verhalend, GEEN bulletpoints.
SCHEMA:
{{
  "sections": [
    {{ "h2": "Kop", "key_points": ["punt 1", "punt 2"], "friction": "Wat is het echte probleem?" }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een Senior Journalist. 
EISEN:
- Schrijf uitsluitend in LOPENDE ALINEA'S. 
- GEEN bulletpoints of genummerde lijsten.
- Toon: Nuchter en verhalend (Avis-stijl).
- VERBODEN: {ban_list}"""

EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. Lever UITSLUITEND JSON.
TAAK:
1. Smeed de tekst aaneen tot een vloeiend essay.
2. VERWIJDER ALLE BULLETPOINTS. Vertaal lijsten naar lopende tekst.
3. LINK-INTEGRATIE: Plaats de marker [ANCHOR_SPOT] op een plek waar de zin grammaticaal klopt als je daar de woorden '{anchor}' invult.
   VOORBEELD: "Veel mensen die hun interieur vernieuwen, besluiten dat het tijd is voor een [ANCHOR_SPOT] bij een specialist."

SCHEMA:
{{
  "title": "Titel", "meta": "Meta", "slug": "slug", "body": "Tekst met ## en [ANCHOR_SPOT]"
}}"""

# --- AI WRAPPER ---
def call_ai(system, prompt, temp=0.7, json_mode=False):
    try:
        args = {"model": "gpt-4o", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}], "temperature": temp}
        if json_mode: args["response_format"] = {"type": "json_object"}
        return client.chat.completions.create(**args).choices[0].message.content
    except Exception as e: return f"ERROR: {str(e)}"

# --- UI ---
st.title("🛡️ Authority Engine v34.1")
st.caption("Narrative Enforcer | Geen Bulletpoints, Geen Losse Links")

with st.sidebar:
    st.header("📋 Master Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    
    st.divider()
    publisher_info = st.text_area("Publisher Context", value="Nuchter woonplatform, focus op echt wonen, geen marketingtaal.")
    page_summary = st.text_area("Product Details", value="Eetkamerstoelen, diverse materialen, focus op zitcomfort.")
    word_count_target = st.slider("Target", 600, 1500, 950)
    start_btn = st.button("EXECUTE NARRATIVE RUN", type="primary")

if start_btn:
    start_time = time.time()
    ban_list = ["oase", "essentieel", "cruciaal", "wereld van verschil", "esthetiek", "harmonie", "samenspel"]

    with st.status("🏗️ Narrative Enforcer in actie...", expanded=True) as status:
        
        # 0. TOPIC LOCK
        topic = call_ai(ANALYZER_SYSTEM, f"URL: {target_url}")
        
        # 1. STRATEGIST
        strat_prompt = f"Target: {word_count_target}w. Topic: {topic}. Publisher: {publisher_info}. GEEN LIJSTJES."
        blueprint_raw = call_ai(STRATEGIST_SYSTEM, strat_prompt, json_mode=True)
        blueprint = json.loads(clean_json_string(blueprint_raw))["sections"]

        # 2. WRITER
        full_draft = ""
        sec_target = word_count_target // len(blueprint)
        for i, section in enumerate(blueprint):
            write_prompt = f"H2: {section['h2']}\nFocus: {section['key_points']}\nFrictie: {section['friction']}\nTARGET: {sec_target} woorden. GEEN BULLETS."
            draft = call_ai(WRITER_SYSTEM.format(ban_list=", ".join(ban_list)), write_prompt)
            full_draft += f"\n\n## {section['h2']}\n{draft}"

        # 3. EDITOR
        editor_sys = EDITOR_SYSTEM.format(anchor=anchor_text, publisher=publisher_info)
        editor_raw = call_ai(editor_sys, f"Smeed aaneen tot een vloeibaar essay van {word_count_target} woorden. Verwijder alle opsommingstekens:\n{full_draft}", json_mode=True)
        final_data = json.loads(clean_json_string(editor_raw))

        # 4. FINAL LINK INJECTION (Hardcoded Markdown)
        body = final_data["body"]
        if "[ANCHOR_SPOT]" in body:
            # We vervangen de marker door de correcte Markdown link
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            # Verwijder eventuele overgebleven markers
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        else:
            # Fallback: als de AI de marker vergat, zoeken we het woord
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            body = pattern.sub(f"[{anchor_text}]({target_url})", body, count=1)
        
        final_data["body"] = body
        status.update(label="✅ Klaar", state="complete")

    # --- OUTPUT ---
    st.metric("Volume", count_words(final_data['body']))
    st.markdown(f"# {final_data['title']}")
    st.markdown(final_data['body'])
    st.download_button("Download Asset", final_data['body'], file_name="asset.md")
