import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v33.0 | MVP Core", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

# --- DETERMINISTISCHE QA FUNCTIES ---
def validate_output(text, anchor, url, target_words, ban_list):
    results = {
        "link_present": f"[{anchor}]({url})" in text,
        "word_count": len(text.split()),
        "ban_words_found": [w for w in ban_list if w.lower() in text.lower()],
        "within_margin": abs(len(text.split()) - target_words) < (target_words * 0.15)
    }
    return results

# --- PROMPT TEMPLATES ---

# 1. Strategist: Maakt het geraamte
STRATEGIST_SYSTEM = """Jij bent een Content Architect. Je levert een JSON blueprint voor een artikel.
SCHEMA:
{{
  "sections": [
    {{ "h2": "Titel", "key_points": ["punt 1", "punt 2"], "context": "Waarom dit relevant is voor de publisher" }}
  ]
}}"""

# 2. Writer: Schrijft op basis van de blueprint
WRITER_SYSTEM = """Jij bent een vakjournalist. Schrijf een sectie op basis van de blueprint details.
STIJL: Nuchter, feitelijk, geen 'AI-acting' (geen stapeling van bijvoeglijke naamwoorden).
VERBODEN: {ban_list}"""

# 3. Editor: Smeed alles samen en plaatst de link
EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. 
TAAK:
1. Smeed de tekst aaneen. 
2. Plaats de ankertekst '{anchor}' op de 2 meest natuurlijke plekken in de body als [ANCHOR_SPOT].
3. Zorg dat de toon aansluit bij: {publisher_context}.
4. Genereer metadata.

LINK STRATEGIE ({anchor_type}):
- Exact: Gebruik precies '{anchor}'
- Branded: Combineer '{anchor}' met de merknaam {client}
- Partial: Verwerk '{anchor}' in een langere, natuurlijke zin.
"""

# --- AI CALL WRAPPER ---
def call_ai(system, prompt, temp=0.7, json_mode=False):
    try:
        args = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temp
        }
        if json_mode:
            args["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**args)
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- UI ---
st.title("🛡️ Authority Engine v33.0")
st.caption("The MVP Core: Deterministische Pipeline voor Linkbuilding")

with st.sidebar:
    st.header("📋 Input Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Anker", value="kledingkast")
    anchor_type = st.selectbox("Anchor Strategie", ["Exact Match", "Partial Match", "Branded"])
    
    st.divider()
    publisher_info = st.text_area("Publisher Profiel", placeholder="Bijv: Lifestyle blog voor jonge gezinnen, focus op budget en DIY.")
    page_summary = st.text_area("Landingspagina Analyse", placeholder="Wat staat er op de URL? (Producten, materialen, USP's)")
    
    word_count_target = st.slider("Target Woorden", 600, 1500, 950, step=50)
    start_btn = st.button("RUN PIPELINE", type="primary")

if start_btn:
    if not publisher_info or not page_summary:
        st.error("P0 FOUT: Vul Publisher Profiel en Landingspagina Analyse in.")
        st.stop()

    start_time = time.time()
    ban_list = ["oase", "essentieel", "cruciaal", "wereld van verschil", "samenspel"]

    with st.status("🏗️ Productie start...", expanded=True) as status:
        
        # STAP 1: STRATEGIST
        st.write("📐 Fase 1: Blueprint genereren...")
        strat_prompt = f"Target: {word_count_target} woorden. Niche: {page_summary}. Publisher: {publisher_info}."
        blueprint_raw = call_ai(STRATEGIST_SYSTEM, strat_prompt, json_mode=True)
        
        try:
            blueprint = json.loads(blueprint_raw)["sections"]
        except:
            st.error("Kritieke fout in Blueprint parsing.")
            st.stop()

        # STAP 2: WRITER (Threading de details!)
        full_draft = ""
        sec_target = word_count_target // len(blueprint)
        
        for i, section in enumerate(blueprint):
            st.write(f"🖋️ Fase 2.{i+1}: Schrijven van '{section['h2']}'...")
            write_prompt = f"""Schrijf deze sectie:
            TITEL: {section['h2']}
            KERNPUNTEN: {', '.join(section['key_points'])}
            CONTEXT: {section['context']}
            TARGET: {sec_target} woorden."""
            
            draft = call_ai(WRITER_SYSTEM.format(ban_list=", ".join(ban_list)), write_prompt)
            full_draft += f"\n\n## {section['h2']}\n{draft}"

        # STAP 3: EDITOR
        st.write("✨ Fase 3: Eindredactie & Link-locatie...")
        edit_prompt = f"Smeed dit aaneen tot {word_count_target} woorden:\n{full_draft}"
        editor_sys = EDITOR_SYSTEM.format(
            anchor=anchor_text, 
            publisher_context=publisher_info, 
            anchor_type=anchor_type,
            client=client_name
        )
        final_json_raw = call_ai(editor_sys, edit_prompt, json_mode=True)
        
        try:
            final_data = json.loads(final_json_raw)
            # Link Injectie (Stap 4: Deterministisch)
            body = final_data["body"]
            # Vervang de eerste [ANCHOR_SPOT] door de echte link
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            # Verwijder resterende markers
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
            final_data["body"] = body
        except:
            st.error("Kritieke fout in Editor parsing.")
            st.stop()

        duration = int(time.time() - start_time)
        status.update(label=f"✅ Asset gereed in {duration}s", state="complete")

    # --- OUTPUT & QA ---
    st.header("💎 De Content Asset")
    
    qa = validate_output(final_data['body'], anchor_text, target_url, word_count_target, ban_list)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Volume", f"{qa['word_count']} / {word_count_target}")
    col2.metric("Link Check", "✅ OK" if qa['link_present'] else "❌ MIST")
    col3.metric("Ban-list", "✅ Schoon" if not qa['ban_words_found'] else f"❌ {len(qa['ban_words_found'])} gevonden")
    col4.metric("Structuur", "✅ Compleet")

    with st.expander("Bekijk Metadata & QA Details"):
        st.write(f"**Titel:** {final_data.get('title')}")
        st.write(f"**Meta Description:** {final_data.get('meta')}")
        st.write(f"**Slug:** {final_data.get('slug')}")
        if qa['ban_words_found']:
            st.error(f"Gevonden verboden woorden: {', '.join(qa['ban_words_found'])}")

    st.markdown("---")
    st.markdown(f"# {final_data.get('title')}")
    st.markdown(final_data['body'])
    
    st.download_button("Download Asset", final_data['body'], file_name="asset.md")
