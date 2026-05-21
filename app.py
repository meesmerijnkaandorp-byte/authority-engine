import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v33.3 | Scannability", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API-sleutel ontbreekt in Secrets.")

# --- ROBUUSTE JSON CLEANER ---
def clean_json_string(raw_string):
    clean = re.sub(r'```json\s*|```', '', raw_string)
    return clean.strip()

def validate_output(text, anchor, url, target_words, ban_list):
    results = {
        "link_present": f"({url})" in text,
        "word_count": len(text.split()),
        "ban_words_found": [w for w in ban_list if w.lower() in text.lower()],
        "scannable": "##" in text or "###" in text
    }
    return results

# --- PROMPT TEMPLATES (v33.3) ---

STRATEGIST_SYSTEM = """Jij bent een Content Architect. Je levert UITSLUITEND JSON.
ONTWERP: Maak een structuur die logisch vloeit, geen herhaling van 'rust' en 'chaos'.
SCHEMA:
{{
  "sections": [
    {{ "h2": "Titel", "key_points": ["punt 1", "punt 2"], "context": "Waarom dit relevant is" }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een nuchtere journalist. Schrijf feitelijk en 'gritty'.
GEBRUIK MARKDOWN: Gebruik **vetgedrukte tekst** voor belangrijke termen.
VERBODEN: {ban_list}, esthetiek, harmonie, samenhangend, prominent."""

EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. Je levert UITSLUITEND JSON.

TAAK:
1. Smeed de tekst aaneen tot een SCANNBAAR artikel.
2. GEBRUIK MARKDOWN: Voeg ## H2 koppen, ### H3 koppen en bulletpoints toe IN de 'body' waarde.
3. LINK-INTEGRATIE: Plaats de marker [ANCHOR_SPOT] exact twee keer. 
   EIS: Zorg dat de zin rondom [ANCHOR_SPOT] grammaticaal klopt als daar de term '{anchor}' staat.
4. STIJL: Verwijder alle 'zweverige' lifestyle-onzin. Blijf zakelijk en nuchter voor: {publisher_context}.

JSON SCHEMA:
{{
  "title": "Kranten-stijl kop",
  "meta": "Zakelijke omschrijving",
  "slug": "url-slug",
  "body": "## Sectie Kop\\n\\nDe tekst met **vetgedrukte woorden** en [ANCHOR_SPOT]..."
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
st.title("🛡️ Authority Engine v33.3")
st.caption("Scannability Update | Weg met de lappen tekst")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Anker", value="eetkamerstoel kopen")
    
    st.divider()
    publisher_info = st.text_area("Publisher", value="Nuchter woonblog, focus op praktische tips.")
    page_summary = st.text_area("Landingspagina", value="Eetkamerstoelen in diverse stijlen, hout, metaal, budgetvriendelijk.")
    word_count_target = st.slider("Target", 600, 1500, 950)
    start_btn = st.button("RUN SCANNABLE PIPELINE", type="primary")

if start_btn:
    start_time = time.time()
    ban_list = ["oase", "essentieel", "cruciaal", "wereld van verschil", "samenspel", "esthetiek", "harmonie"]

    with st.status("🏗️ Productie (v33.3 Formatting Force)...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Blueprint maken...")
        strat_raw = call_ai(STRATEGIST_SYSTEM, f"Target: {word_count_target}w voor {target_url}", json_mode=True)
        blueprint = json.loads(clean_json_string(strat_raw))["sections"]

        # 2. WRITER
        full_draft = ""
        sec_target = word_count_target // len(blueprint)
        for i, section in enumerate(blueprint):
            st.write(f"🖋️ Sectie {i+1} schrijven...")
            write_prompt = f"H2: {section['h2']}\nDetails: {section['key_points']}\nTarget: {sec_target} woorden."
            draft = call_ai(WRITER_SYSTEM.format(ban_list=", ".join(ban_list)), write_prompt)
            full_draft += f"\n\n## {section['h2']}\n{draft}"

        # 3. EDITOR
        st.write("✨ Eindredactie & Opmaak...")
        editor_sys = EDITOR_SYSTEM.format(anchor=anchor_text, publisher_context=publisher_info)
        editor_raw = call_ai(editor_sys, f"Smeed aaneen met Markdown opmaak:\n{full_draft}", json_mode=True)
        
        final_data = json.loads(clean_json_string(editor_raw))
        
        # 4. LINK INJECTION (Met Marker controle)
        body = final_data["body"]
        if "[ANCHOR_SPOT]" in body:
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        else:
            # Fallback: forceer link op eerste match van ankertekst
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            body = pattern.sub(f"[{anchor_text}]({target_url})", body, count=1)
        
        final_data["body"] = body

        status.update(label=f"✅ Klaar in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    qa = validate_output(final_data['body'], anchor_text, target_url, word_count_target, ban_list)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Volume", f"{qa['word_count']}w")
    col2.metric("Link", "✅" if qa['link_present'] else "❌")
    col3.metric("Opmaak", "✅ H2+" if qa['scannable'] else "❌ Plat")
    col4.metric("Ban-list", "✅" if not qa['ban_words_found'] else "❌")

    st.markdown(f"# {final_data['title']}")
    st.markdown(final_article if 'final_article' in locals() else final_data['body'])
    st.sidebar.info(f"Fouten in ban-list: {qa['ban_words_found']}")
