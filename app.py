import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(
    page_title="Authority Engine v19.0 | Enterprise Edition", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Enterprise API Setup
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: OpenAI API-sleutel niet gevonden in de configuratie.")

def count_words(text):
    return len(text.split())

# --- DE REDACTIONELE BIJBEL (De kern van onze kwaliteit) ---
EDITORIAL_GUIDELINES = """
- TOON: Nuchter, autoritair, zakelijk-geïnformeerd. Schrijf voor een volwassen publiek (30-60 jaar).
- VERBODEN WOORDEN: oase, harmonieus, samenspel, ontdekkingsreis, beleving, esthetiek, minimalistisch, 
  cruciaal, essentieel, wereld van verschil, baken, feniks, horizon, prachtig, uniek, krachtig.
- STRUCTUUR: Geen opsommingen (bulletpoints) tenzij technisch noodzakelijk. Gebruik lopende, sterke tekst.
- BENADERING: 'Show, Don't Tell'. Beschrijf situaties (bijv. montage, ruimtegebruik, materiaalgevoel) 
  in plaats van abstracte voordelen.
"""

# --- AGENTEN ---

# 1. De Strategisch Architect
ARCHITECT_PROMPT = f"""Jij bent de Lead Content Strategist. Ontwerp een Paragraph Map voor {{target}} woorden.
URL: {{url}} | KLANT: {{client}} | PLATFORM: {{platform}}

{EDITORIAL_GUIDELINES}

TAAK:
1. Plan 4 substantiële hoofdstukken (H2).
2. Elk hoofdstuk moet een specifiek probleem of een specifieke oplossing behandelen die direct linkt naar {{url}}.
3. Geen algemeenheden. Plan diepgang over materialen, logistiek en dagelijks gebruik.
"""

# 2. De Elite Writer
WRITER_PROMPT = f"""Jij bent een Senior Copywriter met een achtergrond in de journalistiek. 
Je haat marketing-taal en schrijft uitsluitend teksten die 'echt' aanvoelen.

{EDITORIAL_GUIDELINES}

JOUW OPDRACHT:
- Schrijf hoofdstuk {{n}} over {{client}}.
- DOEL: Schrijf exact {{section_target}} woorden. 
- EIS: Gebruik GEEN inleidingen of samenvattingen. Begin direct met de inhoud.
- EIS: Gebruik actieve zinnen. Geen 'wordt gedaan', maar 'je doet'.

{{link_instruction}}
"""

# 3. De Humanizer (Eindredacteur)
ASSEMBLER_PROMPT = f"""Jij bent de Hoofdredacteur. Jouw taak is 'de-robotisering' en technische controle.

{EDITORIAL_GUIDELINES}

TAAK:
1. Smeed de hoofdstukken aaneen tot een vloeiend geheel van {{target}} woorden.
2. LINK GUARD: Zorg dat de link [{{anchor}}]({{url}}) EXACT één keer in de tekst staat. Verwijder duplicaten.
3. SLOP SCAN: Verwijder elke zin die begint met 'Kortom', 'Daarnaast' of 'Het is belangrijk om'.
4. SEO: Genereer Metadata (Title, Meta Description, Slug) die nieuwswaardig is.
"""

# --- ENGINE ---
def call_ai(prompt, system_instruction, temp=0.75):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v19.0")
st.caption("Industrial Content OS | 2026 Enterprise Standards")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("Target URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Publisher Platform", value="dagelijksestandaard.nl")
    
    st.divider()
    word_count_target = st.slider("Target Woordental", 600, 1800, 950, step=50)
    
    start_btn = st.button("RUN PRODUCTION LINE", type="primary")

if start_btn:
    start_time = time.time()
    with st.status("🚀 Engine warmt op...", expanded=True) as status:
        
        # FASE 1: ARCHITECTUUR
        st.write("📐 Fase 1: Strategische Blueprinting...")
        blueprint = call_ai(
            f"Strategie voor {target_url}", 
            ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain, url=target_url)
        )
        
        # FASE 2: SEQUENTIAL PRODUCTION
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int((word_count_target * 1.1) // 4)
        
        for i, s in enumerate(sections):
            # Link instructie: Alleen in sectie 1
            if i == 0:
                l_inst = f"TECHNISCH BEVEL: Verwerk de hyperlink exact zo: [{anchor_text}]({target_url})."
            else:
                l_inst = "GEBRUIK GEEN HYPERLINKS in dit hoofdstuk."
            
            st.write(f"🖋️ Fase 2.{i+1}: Schrijven van Hoofdstuk {i+1}...")
            section_text = call_ai(
                f"Sectie Instructie: {s}",
                WRITER_PROMPT.format(n=i+1, section_target=section_target, client=client_name, link_instruction=l_inst)
            )
            full_raw_content += f"\n\n## {section_text}"
            time.sleep(0.5)

        # FASE 3: ASSEMBLAGE
        st.write("✨ Fase 3: Redactionele Opschoning & Link Guard...")
        final_article = call_ai(
            f"Smeed aaneen en reinig van AI-slop:\n{full_raw_content}", 
            ASSEMBLER_PROMPT.format(target=word_count_target, url=target_url, anchor=anchor_text),
            temp=0.4
        )
        
        duration = int(time.time() - start_time)
        status.update(label=f"✅ Productie Voltooid in {duration}s", state="complete")

    # --- OUTPUT DISPLAY ---
    t1, t2 = st.tabs(["💎 Final Asset", "🧬 Raw Intelligence"])
    
    with t1:
        c_final = count_words(final_article)
        col1, col2, col3 = st.columns(3)
        col1.metric("Volume", f"{c_final} woorden")
        col2.metric("Target", f"{word_count_target}")
        col3.metric("Link Status", "✅ Geplaatst" if f"[{anchor_text}]({target_url})" in final_article else "❌ Mist")
        
        st.markdown("---")
        st.markdown(final_article)
        st.download_button("Export naar Markdown", final_article, file_name=f"{client_name}_asset.md")
        
    with t2:
        st.subheader("Blueprint")
        st.write(blueprint)
        st.subheader("Raw Drafts")
        st.text_area("Secties", full_raw_content, height=300)
