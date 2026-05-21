import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v8.0 | Precision Edition", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (Focus & Volume Planning) ---
ARCHITECT_PROMPT = """Jij bent de Lead Strategist. Ontwerp een Paragraph Map voor exact {target} woorden.
ONDERWERP: {url}
KLANT: {client}
ANKER: {anchor}

EISEN:
1. STRUCTUUR: Maak exact 4 hoofdstukken (H2). Dit beperkt de kans op wildgroei in volume.
2. FOCUS: Schrijf over de specifieke productcategorie van de URL.
3. PLANNING: Verdeel de {target} woorden over deze 4 hoofdstukken.
4. TAAL: Nederlands.
"""

# --- AGENT 2: THE TITAN WRITER (Hyperlink & Style Specialist) ---
WRITER_PROMPT = """Jij bent een bekroonde journalist. Je schrijft menselijk, scherp en technisch perfect.

JOUW OPDRACHT:
Schrijf de tekst voor de toegewezen H2-sectie.
DOEL: Schrijf ongeveer {section_target} woorden.

STRICTE SEO-EIS:
- Je MOET de ankertekst en de URL verwerken als een Markdown hyperlink: [{anchor}]({url}).
- Doe dit op een natuurlijke manier in de lopende tekst. De link mag niet aanvoelen als een advertentie.

STIJL:
- Gebruik 'Show, Don't Tell'. Praat over de realiteit van {client} producten (bijv. kledingkasten).
- GEEN AI-CLICHÉS: Verboden zijn 'baken', 'feniks', 'in de wereld van', 'ontdek', 'navigeren'.
- TAAL: Rijk Nederlands.
"""

# --- AGENT 3: THE ASSEMBLER (Volume Trimmer & Flow) ---
ASSEMBLER_PROMPT = """Jij bent de Eindredacteur. Je smeedt de hoofdstukken aaneen tot een meesterwerk van {target} woorden.

JOUW TAAK:
1. HYPERLINK CHECK: Controleer of de link [{anchor}]({url}) correct aanwezig is. Als de URL los staat, zet hem dan om in de juiste Markdown-hyperlink.
2. VOLUME CONTROLE: Als de totale tekst veel langer is dan {target} woorden, kort dan de meest wollige alinea's in. Wees meedogenloos voor 'fluff'.
3. NARRATIEVE FLOW: Zorg voor vloeiende overgangen.
4. SEO: Voeg Metadata (Title, Meta, Slug) toe bovenaan.
"""

# --- AGENT 4: THE GATEKEEPER (Final Precision Audit) ---
SCORER_PROMPT = """Jij bent de Poortwachter. Beoordeel de tekst op target {target} en de aanwezigheid van de hyperlink.

STRIKTE AFKEUR (Score < 10):
1. De Markdown hyperlink [{anchor}]({url}) ontbreekt.
2. De tekst is meer dan 20% langer of korter dan {target} woorden.

JSON OUTPUT:
{{
    "score": 88,
    "reasoning": "Focus op lengte en link-integratie.",
    "improvements": "Hoe kan het nog korter of krachtiger?"
}}
"""

# --- AI ENGINE ---
def call_ai(prompt, system_instruction, temp=0.8, response_format=None):
    args = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": temp
    }
    if response_format:
        args["response_format"] = response_format
    response = client.chat.completions.create(**args)
    return response.choices[0].message.content

# --- UI ---
st.title("🛡️ Authority Engine v8.0")
st.subheader("Precision Pipeline: Hyperlink Enforced & Volume Controlled")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 1500, 900, step=50)
    
    start_btn = st.button("GENEREER MET PRECISIE", type="primary")

if start_btn:
    with st.status("🏗️ Productie gestart...", expanded=True) as status:
        # FASE 1: ARCHITECT (4 hoofdstukken ipv 5 om volume te beperken)
        st.write("📐 Architect ontwerpt de Paragraph Map...")
        blueprint = call_ai(f"Insteek: Kwaliteitsartikel over de producten op {target_url}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain, url=target_url, anchor=anchor_text))
        
        # FASE 2: WRITER (Buffer verlaagd naar 10%)
        h2_sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int((word_count_target * 1.1) // 4)
        
        for i, s in enumerate(h2_sections):
            st.write(f"🖋️ Writer produceert Hoofdstuk {i+1} (~{section_target} woorden)...")
            section_text = call_ai(
                f"Sectie: {s}\nANKER & URL: [{anchor_text}]({target_url})",
                WRITER_PROMPT.format(section_target=section_target, client=client_name, anchor=anchor_text, url=target_url),
                temp=0.85
            )
            full_raw_content += f"\n\n## {section_text}"
            time.sleep(1)

        # FASE 3: ASSEMBLER (Nu met trim-instructie)
        st.write("✨ Assembler smeedt en trimt de tekst...")
        final_article = call_ai(f"Smeed dit aaneen tot exact {word_count_target} woorden. Trim waar nodig:\n{full_raw_content}", 
                                ASSEMBLER_PROMPT.format(anchor=anchor_text, url=target_url, target=word_count_target), temp=0.7)
        
        # FASE 4: GATEKEEPER
        st.write("🧐 Gatekeeper controleert link en volume...")
        score_raw = call_ai(
            f"Eindtekst:\n\n{final_article}", 
            SCORER_PROMPT.format(target=word_count_target, anchor=anchor_text, url=target_url), 
            temp=0.1, 
            response_format={"type": "json_object"}
        )
        
        score_data = json.loads(score_raw)
        final_score = score_data.get("score", 0)
        
        if final_score >= 85:
            status.update(label=f"✅ Asset Goedgekeurd (Score: {final_score})", state="complete")
        else:
            status.update(label=f"⚠️ Score: {final_score}. Volume of link niet optimaal.", state="error")

    # OUTPUT
    tab1, tab2 = st.tabs(["💎 Final Asset", "📊 Audit"])
    with tab1:
        c_final = count_words(final_article)
        st.metric("Gerealiseerd Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
        st.markdown(final_article)
        st.download_button("Download Markdown", final_article, file_name="export.md")
    with tab2:
        st.json(score_data)
