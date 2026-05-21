import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v33.2 | Brace Fix", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt in Secrets.")

# --- ROBUUSTE JSON CLEANER ---
def clean_json_string(raw_string):
    """Verwijdert AI-gebabbel en markdown blocks rondom JSON."""
    clean = re.sub(r'```json\s*|```', '', raw_string)
    return clean.strip()

def validate_output(text, anchor, url, target_words, ban_list):
    results = {
        "link_present": f"[{anchor}]({url})" in text,
        "word_count": len(text.split()),
        "ban_words_found": [w for w in ban_list if w.lower() in text.lower()],
        "within_margin": abs(len(text.split()) - target_words) < (target_words * 0.20)
    }
    return results

# --- PROMPT TEMPLATES (Met escaped accolades voor JSON) ---

STRATEGIST_SYSTEM = """Jij bent een Content Architect. Je levert UITSLUITEND JSON.
SCHEMA:
{{
  "sections": [
    {{ "h2": "Titel", "key_points": ["punt 1", "punt 2"], "context": "Waarom dit relevant is voor de publisher" }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een vakjournalist. Schrijf nuchter en feitelijk.
VERBODEN WOORDEN: {ban_list}"""

EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. Je levert UITSLUITEND JSON.
TAAK:
1. Smeed de tekst aaneen.
2. Plaats exact twee keer de marker [ANCHOR_SPOT] op natuurlijke plekken voor de term '{anchor}'.
3. Gebruik de stijl van: {publisher_context}.

JSON SCHEMA:
{{
  "title": "Strakke kop",
  "meta": "Meta omschrijving",
  "slug": "url-slug",
  "body": "De volledige tekst met [ANCHOR_SPOT] markers..."
}}"""

# --- AI CALL WRAPPER ---
def call_ai(system, prompt, temp=0.7, json_mode=False):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=temp,
            response_format={"type": "json_object"} if json_mode else None
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- UI ---
st.title("🛡️ Authority Engine v33.2")
st.caption("Brace Fix Edition | JSON & Python Harmony")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Anker", value="kledingkast")
    anchor_type = st.selectbox("Strategie", ["Exact Match", "Partial Match", "Branded"])
    
    st.divider()
    publisher_info = st.text_area("Publisher Profiel", value="Lifestyle blog, nuchtere toon.")
    page_summary = st.text_area("Landingspagina Analyse", value="Kledingkasten, diverse materialen, focus op budget.")
    word_count_target = st.slider("Target", 600, 1500, 950)
    start_btn = st.button("RUN STABLE PIPELINE", type="primary")

if start_btn:
    start_time = time.time()
    ban_list = ["oase", "essentieel", "cruciaal", "wereld van verschil"]

    with st.status("🏗️ Productie in uitvoering...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Blueprint genereren...")
        # De strategist prompt heeft geen format nodig voor variabelen, dus we laten hem zo.
        strat_raw = call_ai(STRATEGIST_SYSTEM, f"Target: {word_count_target}w voor {target_url}", json_mode=True)
        try:
            blueprint = json.loads(clean_json_string(strat_raw))["sections"]
        except Exception as e:
            st.error(f"Blueprint Error: {e}")
            st.code(strat_raw)
            st.stop()

        # 2. WRITER
        full_draft = ""
        sec_target = word_count_target // len(blueprint)
        for i, section in enumerate(blueprint):
            st.write(f"🖋️ Sectie {i+1} schrijven...")
            write_prompt = f"H2: {section['h2']}\nPunten: {section['key_points']}\nTarget: {sec_target} woorden."
            draft = call_ai(WRITER_SYSTEM.format(ban_list=", ".join(ban_list)), write_prompt)
            full_raw_section = f"\n\n## {section['h2']}\n{draft}"
            full_draft += full_raw_section

        # 3. EDITOR
        st.write("✨ Eindredactie & JSON-assemblage...")
        # Hier gebeurde de KeyError. Nu gefixt met dubbele accolades in de constante.
        editor_sys = EDITOR_SYSTEM.format(anchor=anchor_text, publisher_context=publisher_info)
        editor_raw = call_ai(editor_sys, f"Smeed aaneen:\n{full_draft}", json_mode=True)
        
        try:
            final_data = json.loads(clean_json_string(editor_raw))
            # Link Injectie
            body = final_data["body"]
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
            final_data["body"] = body
        except Exception as e:
            st.error(f"Editor Parsing Fout: {e}")
            st.subheader("Raw Output voor debug (check op ongeclosede quotes):")
            st.code(editor_raw)
            st.stop()

        duration = int(time.time() - start_time)
        status.update(label=f"✅ Klaar in {duration}s", state="complete")

    # --- OUTPUT ---
    qa = validate_output(final_data['body'], anchor_text, target_url, word_count_target, ban_list)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Volume", f"{qa['word_count']}w")
    col2.metric("Link", "✅" if qa['link_present'] else "❌")
    col3.metric("Ban-list", "✅" if not qa['ban_words_found'] else "❌")

    st.markdown(f"# {final_data['title']}")
    st.markdown(final_data['body'])
    st.sidebar.success("Asset succesvol gegenereerd!")
