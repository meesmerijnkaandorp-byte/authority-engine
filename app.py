import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v35.0 | Versatile Authority", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt in Secrets.")

# --- UTILS ---
def count_words(text):
    return len(text.split())

def clean_json_string(raw_string):
    clean = re.sub(r'```json\s*|```', '', raw_string)
    return clean.strip()

# --- SYSTEM PROMPTS (v35.0) ---

STRATEGIST_SYSTEM = """Jij bent een Content Architect. Je levert UITSLUITEND JSON.
TAAK: Ontwerp een essay-structuur van {target} woorden.
EIS: Plan uitsluitend LOPENDE tekst. GEEN opsommingen of lijstjes.
SCHEMA:
{{
  "sections": [
    {{ "h2": "Kop", "key_points": ["punt 1", "punt 2"], "friction": "Het onderliggende probleem" }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een Senior Journalist. Schrijf rauw, feitelijk en zonder franje.
STRICTE EISEN:
1. GEEN BULLETPOINTS. Gebruik uitsluitend volledige alinea's.
2. TOON: Nuchter en observerend (denk aan de 'zaterdagmorgen-energie').
3. DETAILS: Benoem materialen, gewicht, geluid en weerstand.
4. VERBODEN: {ban_list}"""

EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. Je levert UITSLUITEND JSON.
TAAK:
1. Smeed de hoofdstukken aaneen tot een naadloos essay van {target} woorden.
2. VERWIJDER ELKE BULLETPOINT. Vertaal lijsten naar sterke, vloeiende alinea's.
3. LINK-INTEGRATIE: Plaats de marker [ANCHOR_SPOT] op een plek waar de zin klopt met '{anchor}'.
   
LINK-LOGICA ({a_mode}):
- Exact Match: De zin MOET grammaticaal kloppen met de exacte woorden '{anchor}'. 
- Natuurlijk: Je mag de ankertekst licht aanpassen (meervoud/verbuiging) voor een perfecte loop.

SCHEMA:
{{
  "title": "Titel", "meta": "Meta", "slug": "slug", "body": "## Kop\\n\\nTekst met [ANCHOR_SPOT]..."
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

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v35.0")
st.caption("Versatile Authority Engine | Exact Match & Narrative Integrity")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    anchor_mode = st.radio("Link Modus", ["Exact Match", "Natuurlijk/Vloeiend"])
    
    st.divider()
    publisher_context = st.text_area("Publisher", value="Lifestyle blog, volwassen publiek, nuchtere toon.")
    page_summary = st.text_area("Landingspagina", value="Eetkamerstoelen, diverse materialen (hout/metaal), focus op prijs-kwaliteit.")
    word_count_target = st.slider("Target Woorden", 600, 1500, 950)
    start_btn = st.button("PRODUCEER ASSET", type="primary")

if start_btn:
    start_time = time.time()
    ban_list = ["oase", "essentieel", "cruciaal", "wereld van verschil", "esthetiek", "harmonie", "samenspel"]

    with st.status("🏗️ Sovereign Pipeline v35.0 activeert...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Blueprinting (No-List Policy)...")
        strat_sys = STRATEGIST_SYSTEM.format(target=word_count_target)
        blueprint_raw = call_ai(strat_sys, f"Topic: {anchor_text}. Context: {page_summary}", json_mode=True)
        blueprint = json.loads(clean_json_string(blueprint_raw))["sections"]

        # 2. WRITER
        full_draft = ""
        sec_target = word_count_target // len(blueprint)
        for i, section in enumerate(blueprint):
            st.write(f"🖋️ Schrijven hoofdstuk {i+1}...")
            write_prompt = f"H2: {section['h2']}\nKey points: {section['key_points']}\nFrictie: {section['friction']}\nTarget: {sec_target} woorden. GEEN LIJSTEN."
            draft = call_ai(WRITER_SYSTEM.format(ban_list=", ".join(ban_list)), write_prompt)
            full_draft += f"\n\n## {section['h2']}\n{draft}"

        # 3. EDITOR (The Link Surgeon)
        st.write("✨ Eindredactie & Link Injectie...")
        editor_sys = EDITOR_SYSTEM.format(target=word_count_target, anchor=anchor_text, a_mode=anchor_mode, publisher_context=publisher_context)
        editor_raw = call_ai(editor_sys, f"Smeed aaneen tot vloeiend essay:\n{full_draft}", json_mode=True)
        final_data = json.loads(clean_json_string(editor_raw))

        # 4. FINAL POLISH
        body = final_data["body"]
        if "[ANCHOR_SPOT]" in body:
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        else:
            # Fallback regex
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            body = pattern.sub(f"[{anchor_text}]({target_url})", body, count=1)
        
        final_data["body"] = body
        status.update(label=f"✅ Gereed in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    st.metric("Gerealiseerd Volume", count_words(final_data['body']), delta=int(count_words(final_data['body']) - word_count_target))
    
    st.markdown(f"# {final_data['title']}")
    st.markdown(final_data['body'])
    
    with st.expander("Audit & Metadata"):
        st.write(f"**Meta:** {final_data['meta']}")
        st.write(f"**Slug:** {final_data['slug']}")
        st.write(f"**Link Mode:** {anchor_mode}")
