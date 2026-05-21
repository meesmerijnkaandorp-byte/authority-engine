import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE & SETUP ---
st.set_page_config(page_title="Authority Engine v31.0 | Marketplace Pro", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: OpenAI API-sleutel ontbreekt. Check je Streamlit Secrets.")

def count_words(text):
    return len(text.split())

# --- DE REDACTIONELE STANDAARD (Niche-Agnostisch) ---
GLOBAL_BAN_LIST = [
    "oase", "harmonie", "samenspel", "essentieel", "cruciaal", "wereld van verschil", 
    "baken", "feniks", "paradigma", "beleving", "ontdek", "uniek", "perfect", 
    "tand des tijds", "geoliede machine", "in de moderne wereld", "is van groot belang"
]

# --- AGENT PROMPTS ---

# 1. De Strateeg (Analyseert Niche & Publisher)
STRATEGIST_PROMPT = """Jij bent een Senior Content Planner. Ontwerp een artikel-blueprint op basis van:
KLANT: {client} | NICHE: {niche} | PUBLISHER: {publisher_info} | TARGET: {target} woorden.

TAAK:
1. Analyseer de toon van de publisher.
2. Plan 4 secties (H2) die NIET promotioneel zijn.
3. Focus op 'High Utility Content': informatie waar de lezer echt iets aan heeft.
4. Identificeer de 'frictie' in deze niche (bijv. bij Finance: onbegrijpelijk jargon; bij Home: montage-ellende).

OUTPUT: Lever een JSON-blueprint met 4 secties en per sectie 3 kernpunten.
"""

# 2. De Ghostwriter (Focust op realisme, niet op poëzie)
WRITER_PROMPT = """Jij bent een nuchtere vakjournalist. Schrijf hoofdstuk {n} over {section_title}.
STIJL:
- Gebruik 'Low-Key Realism'. Geen overdreven zintuiglijke stapeling.
- Gebruik specifieke feiten, handelingen en gevolgen.
- VERBODEN: {ban_list}
- TONE: Pas je aan aan de publisher: {publisher_info}

DOEL: {section_target} woorden. Geen inleiding, direct ter zake.
"""

# 3. De Editor & Link Manager (Structured Output)
EDITOR_PROMPT = """Jij bent de Hoofdredacteur. Je krijgt een ruwe tekst voor {client}.
TAAK:
1. Smeed de tekst aaneen tot een vloeiend geheel van {target} woorden.
2. Verwijder alle 'AI-vulling' en gladde overgangen.
3. Identificeer in de tekst de 3 meest natuurlijke plekken voor de ankertekst '{anchor}'.
4. Genereer metadata.

OUTPUT MOET STRIKTE JSON ZIJN:
{{
  "title": "...",
  "meta": "...",
  "slug": "...",
  "body": "De volledige tekst met [ANCHOR_SPOT] op de 3 beste plekken.",
  "qc_score": 0-100,
  "audit_notes": "..."
}}
"""

# --- ENGINE FUNCTIES ---

def get_ai_response(prompt, system_instruction, temp=0.7, json_mode=False):
    try:
        response_format = {"type": "json_object"} if json_mode else None
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=temp,
            response_format=response_format
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- UI INTERFACE ---
st.title("🚀 Authority Engine v31.0")
st.caption("Marketplace Production Engine | Built for Scale & Quality")

with st.sidebar:
    st.header("📋 Order Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    niche = st.selectbox("Niche", ["Huis & Tuin", "Lifestyle", "Finance", "B2B", "Tech", "Travel", "Health"])
    publisher_desc = st.text_area("Publisher Context", placeholder="Bijv: Landelijk nieuwsplatform, nuchtere toon, focus op besparen.")
    
    st.divider()
    target_url = st.text_input("Target URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    anchor_type = st.radio("Anchor Type", ["Exact Match", "Partial Match", "Branded", "Generic"])
    
    word_count_target = st.slider("Target Woorden", 600, 1500, 950, step=50)
    
    start_btn = st.button("EXECUTE PRODUCTION", type="primary")

if start_btn:
    start_time = time.time()
    with st.status("🏗️ Engine draait...", expanded=True) as status:
        
        # 1. ANALYSE & BLUEPRINT
        st.write("📐 Fase 1: Blueprint genereren...")
        strat_sys = STRATEGIST_PROMPT.format(
            client=client_name, niche=niche, publisher_info=publisher_desc, target=word_count_target
        )
        blueprint_json = get_ai_response("Start blueprinting", strat_sys, json_mode=True)
        blueprint = json.loads(blueprint_json)
        
        # 2. SECTIE PRODUCTIE
        full_draft = ""
        section_target = word_count_target // 4
        
        for i, (title, details) in enumerate(blueprint.items()):
            if i >= 4: break # Safety
            st.write(f"🖋️ Fase 2.{i+1}: Schrijven sectie '{title}'...")
            writer_sys = WRITER_PROMPT.format(
                n=i+1, section_title=title, section_details=details, 
                section_target=section_target, ban_list=", ".join(GLOBAL_BAN_LIST),
                publisher_info=publisher_desc
            )
            section_draft = get_ai_response(f"Schrijf sectie {i+1}", writer_sys)
            full_draft += f"\n\n## {title}\n{section_text if 'section_text' in locals() else section_draft}"
        
        # 3. EDITORIAL & LINK INJECTION
        st.write("✨ Fase 3: Redactie & Structured Output...")
        editor_sys = EDITOR_PROMPT.format(
            target=word_count_target, client=client_name, anchor=anchor_text, url=target_url
        )
        final_json_raw = get_ai_response(f"Editoriaal polijsten van:\n{full_draft}", editor_sys, temp=0.5, json_mode=True)
        
        try:
            final_data = json.loads(final_json_raw)
            # Link Injection Logica: We pakken de 2e [ANCHOR_SPOT] voor een natuurlijke flow
            body_with_link = final_data["body"].replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body_with_link = body_with_link.replace("[ANCHOR_SPOT]", anchor_text) # De rest van de spots worden gewone tekst
            final_data["body"] = body_with_link
        except Exception as e:
            st.error(f"Assemblage fout: {e}")
            final_data = {"body": full_draft, "title": "Error in JSON"}

        duration = int(time.time() - start_time)
        status.update(label=f"✅ Asset Gereed in {duration}s", state="complete")

    # --- OUTPUT ---
    t1, t2, t3 = st.tabs(["📄 Final Asset", "📊 Audit & Meta", "⚙️ Raw Data"])
    
    with t1:
        st.metric("Gerealiseerd Volume", count_words(final_data['body']), delta=int(count_words(final_data['body']) - word_count_target))
        st.markdown(f"# {final_data.get('title', 'Geen titel')}")
        st.markdown(final_data['body'])
        
    with t2:
        st.subheader("SEO Metadata")
        st.code(f"Title: {final_data.get('title')}\nMeta: {final_data.get('meta')}\nSlug: {final_data.get('slug')}")
        st.divider()
        st.subheader("Audit Notes")
        st.info(final_data.get("audit_notes", "Geen opmerkingen."))
        st.progress(final_data.get("qc_score", 0) / 100, text=f"QC Score: {final_data.get('qc_score')}%")

    with t3:
        st.json(final_data)
        st.download_button("Download JSON Asset", json.dumps(final_data, indent=2), file_name="export.json")
