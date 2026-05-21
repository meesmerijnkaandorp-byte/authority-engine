import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v36.0 | Linguistic Surgeon", layout="wide")

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

# --- SYSTEM PROMPTS (v36.0) ---

STRATEGIST_SYSTEM = """Jij bent een Content Architect. Je levert UITSLUITEND JSON.
TAAK: Ontwerp een essay-structuur van {target} woorden. 
EIS: Geen inleidingen over 'belangrijkheid'. Focus op de frictie van het onderwerp.
SCHEMA:
{{
  "sections": [
    {{ "h2": "Kop", "key_points": ["punt 1", "punt 2"], "friction": "Waarom het in de praktijk vaak misgaat" }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een Senior Journalist. Schrijf rauw en feitelijk.
STRICTE EISEN:
1. GEEN LIJSTJES. Gebruik uitsluitend lopende tekst.
2. VERBODEN WOORDEN: {ban_list}, cruciale rol, essentieel, esthetiek, harmonie, samenspel.
3. FOCUS: Gebruik concrete details (gewicht, materiaal, geluid)."""

EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. Je levert UITSLUITEND JSON.
TAAK: Smeed de tekst aaneen tot een vloeiend essay van {target} woorden.

LINK-INTEGRATIE ({a_mode}):
Je MOET de marker [ANCHOR_SPOT] verwerken in een zin die grammaticaal perfect loopt met de term '{anchor}'.
Hanteer voor '{anchor}' een van deze structuren:
- "Wie overweegt een [ANCHOR_SPOT], doet er goed aan te letten op..."
- "Het proces van een [ANCHOR_SPOT] wordt vaak onderschat door..."
- "In de zoektocht naar een [ANCHOR_SPOT] bij een specialist als {client} valt op dat..."

SCHEMA:
{{
  "title": "Titel", "meta": "Meta", "slug": "slug", "body": "Tekst met [ANCHOR_SPOT]"
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
    except Exception as e: return f"ERROR: {str(e)}"

# --- UI ---
st.title("🛡️ Authority Engine v36.0")
st.caption("The Linguistic Surgeon | Geen loshangende ankerteksten meer")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    anchor_mode = st.radio("Link Modus", ["Exact Match", "Natuurlijk/Vloeiend"])
    
    st.divider()
    publisher_context = st.text_area("Publisher", value="Nuchter woonblog, geen marketing-bullshit.")
    word_count_target = st.slider("Target Woorden", 600, 1500, 950)
    start_btn = st.button("PRODUCEER ASSET", type="primary")

if start_btn:
    start_time = time.time()
    # Uitgebreide zwarte lijst met de clichés uit je feedback
    ban_list = ["oase", "wereld van verschil", "belangrijkste rol", "fundamentele rol", "cruciaal", "essentieel"]

    with st.status("🏗️ Taalkundige operatie bezig...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Blueprinting...")
        strat_sys = STRATEGIST_SYSTEM.format(target=word_count_target)
        blueprint_raw = call_ai(strat_sys, f"Onderwerp: {anchor_text}. Context: {publisher_context}", json_mode=True)
        blueprint = json.loads(clean_json_string(blueprint_raw))["sections"]

        # 2. WRITER
        full_draft = ""
        sec_target = word_count_target // len(blueprint)
        for i, section in enumerate(blueprint):
            st.write(f"🖋️ Hoofdstuk {i+1} schrijven...")
            write_prompt = f"H2: {section['h2']}\nFocus: {section['key_points']}\nFrictie: {section['friction']}\nTarget: {sec_target}w."
            draft = call_ai(WRITER_SYSTEM.format(ban_list=", ".join(ban_list)), write_prompt)
            full_draft += f"\n\n## {section['h2']}\n{draft}"

        # 3. EDITOR
        st.write("✨ Chirurgische link-injectie...")
        editor_sys = EDITOR_SYSTEM.format(target=word_count_target, anchor=anchor_text, a_mode=anchor_mode, client=client_name, publisher=publisher_context)
        editor_raw = call_ai(editor_sys, f"Smeed aaneen en integreer de link naadloos:\n{full_draft}", json_mode=True)
        final_data = json.loads(clean_json_string(editor_raw))

        # 4. PYTHON POST-PROCESS
        body = final_data["body"]
        # We zorgen voor een spatie-correcte vervanging
        link_markdown = f"[{anchor_text}]({target_url})"
        body = body.replace("[ANCHOR_SPOT]", link_markdown, 1)
        body = body.replace("[ANCHOR_SPOT]", anchor_text)
        
        final_data["body"] = body
        status.update(label="✅ Asset gereed", state="complete")

    # --- OUTPUT ---
    st.metric("Gerealiseerd Volume", count_words(final_data['body']))
    st.markdown(f"# {final_data['title']}")
    st.markdown(final_data['body'])
    
    with st.expander("Audit"):
        st.write(f"**Anker gebruikt:** {anchor_text}")
        st.write(f"**Link aanwezig:** {'Ja' if f'({target_url})' in final_data['body'] else 'Nee'}")
