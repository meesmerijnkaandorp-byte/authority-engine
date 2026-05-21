import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v25.0 | The Master Directive", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel niet gevonden in Secrets.")

def count_words(text):
    return len(text.split())

# --- DE GOUDEN STANDAARD (Lifestyle & Grit) ---
STIJL_RICHTLIJN = """
Kopieer de energie van dit voorbeeld: nuchter, beschouwend, menselijk.
"Een huis fungeert als tegenwicht voor de drukte buiten. Een opgeruimde omgeving helpt om je hoofd leeg te maken. 
Het gaat om het gevoel dat de ruimte je ondersteunt in plaats van afleidt."
"""

# --- AGENT PROMPTS ---

ARCHITECT_PROMPT = f"""Jij bent een Hoofdredacteur van een kwaliteitsmedium. 
Ontwerp een essay-structuur voor {{target}} woorden over {{url}}.

DOEL: Schrijf een diepgaand lifestyle-essay over mentale rust en de fysieke inrichting van je huis.

HOOFDSTUKKEN (H2):
1. De psychologie van de drempel: Hoe de chaos van buiten je huis binnendringt.
2. De slaapkamer als laatste fort: Waarom visuele rust hier essentieel is voor je herstel.
3. De anatomie van orde: Hoe een goede {{anchor}} fungeert als het fundament van een opgeruimd leven.
4. De kunst van het weglaten: Waarom minder bezit leidt tot meer mentale ademruimte.

RICHTLIJN: {STIJL_RICHTLIJN}
"""

WRITER_PROMPT = """Jij bent een Senior Essayist. Je schrijft teksten met 'textuur'.

STIJLREGELS:
- TOON: Nuchter en reflectief. 
- DETAILS: Benoem tastbare zaken: het geluid van een hanger, de geur van linnen, het gewicht van een winterjas, de koelte van een handgreep.
- VERBODEN (AI-SLOP): oase, harmonie, samenspel, ontdek, essentieel, cruciaal, wereld van verschil, beleving, uniek, prachtig.
- ZINSBOUW: Varieer. Gebruik korte, krachtige zinnen voor nadruk.

DOEL: Schrijf minimaal {section_target} woorden voor deze sectie.
"""

ASSEMBLER_PROMPT = """Jij bent de eindredacteur. Smeed de hoofdstukken aaneen tot één meesterwerk.
1. VERWIJDER: Elke zin die klinkt als een verkoop-praatje of een handleiding.
2. VERBETER: Zorg dat de overgang tussen psychologische rust en de praktische oplossing (de kast) natuurlijk voelt.
3. VOLUME: Trim of breid uit tot we rond de {target} woorden zitten.
4. SEO: Title, Meta Description (max 155 tekens), Slug.
"""

# --- AI ENGINE ---
def call_ai(prompt, system_instruction, temp=0.8):
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
st.title("🛡️ Authority Engine v25.0")
st.subheader("The Master Directive | Lifestyle Content for 2026")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL")
    target_url = st.text_input("Target URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    word_count_target = st.slider("Target Woorden", 600, 1500, 950, step=50)
    
    st.divider()
    start_btn = st.button("EXECUTE PRODUCTION", type="primary")

if start_btn:
    start_time = time.time()
    with st.status("🏗️ Essay wordt geweven...", expanded=True) as status:
        
        # FASE 1: ARCHITECT
        st.write("📐 Architectuur ontwerpen...")
        blueprint = call_ai(f"Plan voor {target_url}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, url=target_url, client=client_name, anchor=anchor_text))
        
        # FASE 2: WRITING
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        # Precisie-berekening: target gedeeld door 4 secties, kleine marge voor de Assembler.
        section_target = int(word_count_target // 4)
        
        for i, s in enumerate(sections):
            st.write(f"🖋️ Essayist produceert hoofdstuk {i+1}...")
            section_text = call_ai(f"Sectie: {s}", WRITER_PROMPT.format(section_target=section_target, anchor=anchor_text))
            full_raw_content += f"\n\n## {section_text}"

        # FASE 3: ASSEMBLY
        st.write("✨ Redactionele polijstfase...")
        final_article = call_ai(f"Assemblage van:\n{full_raw_content}", ASSEMBLER_PROMPT.format(target=word_count_target), temp=0.5)
        
        # FASE 4: PYTHON IRON-LINK INJECTION
        # We zoeken de eerste 'kledingkast' (ongeacht hoofdletters) en maken er een link van.
        pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
        # We doen de vervanging alleen als de link er nog niet in staat.
        if f"]({target_url})" not in final_article:
            final_article = pattern.sub(f"[{anchor_text}]({target_url})", final_article, count=1)

        status.update(label=f"✅ Asset voltooid in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    c_final = count_words(final_article)
    st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
    
    st.markdown("---")
    st.markdown(final_article)
    st.download_button("Download Asset (.md)", final_article, file_name=f"{client_name}_lifestyle_essay.md")
