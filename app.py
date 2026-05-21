import streamlit as st
from openai import OpenAI
import time

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Proprietary Content OS v2.0", layout="wide")

# Beveiliging & API
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel niet geconfigureerd in Streamlit Secrets.")

def count_words(text):
    return len(text.split())

# --- PROMPT 1: THE ARCHITECT (Outline & Research) ---
ARCHITECT_PROMPT = """Jij bent de Lead Content Strategist. Jouw taak is om een diepgaande, journalistieke outline te maken voor een artikel van {target} woorden.
Je moet het onderwerp opdelen in 4 substantiële hoofdstukken (H2). 
Elk hoofdstuk moet een specifieke invalshoek hebben die de diepgang garandeert. 
Stuur alleen de outline terug (H1 en de H2's met korte beschrijving per H2)."""

# --- PROMPT 2: THE ELITE WRITER (Section Focused) ---
WRITER_PROMPT = """Jij bent een Senior Essayist voor bladen als 'Atlantic' of 'Wired'. 
Jouw schrijfstijl is grillig, menselijk, diepgaand en vrij van AI-clichés.

JOUW OPDRACHT:
Schrijf alleen de tekst voor de specifieke sectie die je wordt toegewezen. 
DOEL: Schrijf minimaal {section_target} woorden voor DEZE sectie alleen. 
STIJLREGELS:
- Gebruik complexe zinsstructuren en varieer met korte, krachtige statements.
- Gebruik GEEN marketing-jargon ('ontdek', 'uniek', 'oplossing').
- Gebruik 'low-frequency' woorden en weef de ankertekst organisch in het betoog.
- Focus op de 'waarom' en 'hoe', niet alleen de 'wat'.
- Geen sub-headers (H3) tenzij absoluut noodzakelijk voor technische complexiteit.
"""

# --- PROMPT 3: THE POLISHER (Assembly & Narrative Flow) ---
POLISHER_PROMPT = """Jij bent een Eindredacteur. Je krijgt een artikel dat in delen is geschreven. 
Jouw taak is om de 'narratieve lijm' aan te brengen. 
- Zorg voor soepele overgangen tussen de alinea's en hoofdstukken.
- Verwijder eventuele herhalingen die zijn ontstaan door het stapsgewijs schrijven.
- Voeg SEO Metadata (Title, Meta, Slug) toe aan de top van het document.
- Zorg dat de tone-of-voice consistent, autoritair en intellectueel uitdagend is over het hele stuk.
"""

# --- PROMPT 4: THE TYRANT AUDITOR (Final Quality Gate) ---
AUDITOR_PROMPT = """Jij bent de meest gevreesde Editor-in-Chief. Je haat AI-slop en oppervlakkigheid.
JOUW TAKEN:
1. WOORDEN-CHECK: Is het artikel substantieel en voldoet het aan het doel?
2. AI-VINGERAFDRUK: Scan op voorspelbare patronen en vervang ze door scherpere journalistiek.
3. E-E-A-T: Straalt deze tekst uit dat het geschreven is door een mens met 20 jaar ervaring?
Geef een score en finale verbeterpunten."""

# --- ENGINE FUNCTIE ---
def call_ai(prompt, system_instruction, model="gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.85
    )
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🛡️ Proprietary Content OS v2.0")
st.subheader("Sequential Authority Architecture")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", "Bijv. Managed Hosting Pro")
    target_domain = st.text_input("Platform", "Bijv. techcrunch.com")
    
    st.divider()
    word_count_target = st.slider("Target Woorden", 600, 2000, 1000, step=100)
    
    st.divider()
    link_1 = st.text_input("URL 1")
    anchor_1 = st.text_input("Anchor 1")
    link_2 = st.text_input("URL 2 (Optioneel)")
    anchor_2 = st.text_input("Anchor 2")
    
    subject = st.text_area("Insteek", placeholder="Optioneel: Geef specifieke hoek aan...")
    
    start_btn = st.button("START PRODUCTION PIPELINE", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Kritieke data ontbreekt in de briefing.")
    else:
        # FASE 1: DE ARCHITECT
        with st.status("🏗️ Fase 1: Architectuur ontwerpen...", expanded=True) as status:
            outline = call_ai(f"Onderwerp: {subject if subject else 'Autoriteit artikel'}. Klant: {client_name}. Platform: {target_domain}. Doel: {word_count_target} woorden.", ARCHITECT_PROMPT)
            st.write("Outline gegenereerd.")
            
            # FASE 2: DE WRITER (SERIAL GENERATION)
            sections = outline.split("##")[1:] # Haal de H2's eruit
            full_draft = ""
            section_target = (word_count_target // len(sections)) + 100 # Ruime marge per sectie
            
            for i, section in enumerate(sections):
                st.write(f"🖋️ Fase 2.{i+1}: Hoofdstuk {i+1} schrijven ({section_target} woorden)...")
                section_content = call_ai(f"Schrijf dit hoofdstuk voor {target_domain} over {client_name}. Sectie details: {section}. Gebruik links: {link_1} ({anchor_1}) en {link_2} ({anchor_2}) indien passend.", WRITER_PROMPT.format(section_target=section_target))
                full_draft += f"\n\n## {section_content}"
                time.sleep(1) # Rate limit protectie
            
            # FASE 3: ASSEMBLY & POLISH
            status.update(label="✨ Fase 3: Assemblage & Narratieve Flow...", state="running")
            final_article = call_ai(f"Klant: {client_name}. Platform: {target_domain}. Hier is de ruwe tekst van alle secties:\n\n{full_draft}", POLISHER_PROMPT)
            
            # FASE 4: FINAL AUDIT
            status.update(label="🧐 Fase 4: Finale Kwaliteitscontrole...", state="running")
            audit_report = call_ai(f"Target: {word_count_target} woorden. Tekst:\n\n{final_article}", AUDITOR_PROMPT)
            
            status.update(label="✅ Productie Voltooid", state="complete")

        # --- OUTPUT ---
        t1, t2, t3 = st.tabs(["💎 Final Asset", "🔍 Audit Rapport", "🧬 Blueprint"])
        
        with t1:
            c_final = count_words(final_article)
            st.metric("Final Word Count", f"{c_final} woorden", delta=int(c_final - word_count_target))
            st.markdown(final_article)
            st.download_button("Export voor CMS", final_article, file_name=f"{client_name}_final.md")
            
        with t2:
            st.markdown(audit_report)
            
        with t3:
            st.markdown(outline)
            st.text_area("Rauwe Secties", full_draft, height=300)
