import streamlit as st
from openai import OpenAI
import time
import re

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v18.0 | Commercial Standard", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("API-sleutel niet geconfigureerd.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (Content Planner) ---
ARCHITECT_PROMPT = """Jij bent een Content Planner voor een online magazine. 
Ontwerp een structuur voor een commercieel blogartikel van {target} woorden.

DOEL: 
- Informeer de lezer over het belang van een goede kledingkast en opbergsystemen.
- Maak het herkenbaar en praktisch.
- Plan 4 logische hoofdstukken (H2) die de lezer van het probleem (chaos) naar de oplossing (slim inrichten) leiden.
- GEEN poëzie, GEEN zweverige metaforen. Gewoon een goed verhaal voor een breed publiek.
"""

# --- AGENT 2: THE WRITER (Professional Copywriter) ---
WRITER_PROMPT = """Jij bent een ervaren Copywriter. Je schrijft vlotte, informatieve artikelen voor commerciële blogs.

STIJLREGELS:
- TOON: Behulpzaam, deskundig en vlot. 
- GEEN MARKETING-CLICHÉS: Vermijd 'oase', 'essentieel', 'cruciaal', 'samenspel', 'ontdek', 'wereld van verschil'.
- GEEN POËZIE: Schrijf geen abstracte verhalen over wekkers of exorcisme. Praat over interieur, ruimte en gebruiksgemak.
- STRUCTUUR: Gebruik normale alinea's.

{link_instruction}

DOEL: Schrijf ongeveer {section_target} woorden voor deze sectie.
"""

# --- AGENT 3: THE ASSEMBLER (Eindredacteur) ---
ASSEMBLER_PROMPT = """Jij bent de eindredacteur. Smeed de teksten aaneen tot een vloeiend artikel van {target} woorden.

TAKEN:
1. Controleer de link: [{anchor}]({url}) mag exact één keer voorkomen.
2. Verwijder zweverige taal of vreemde metaforen.
3. Zorg voor een logische opbouw voor een commerciële publisher.
4. Voeg Metadata toe: Title, Meta Description, Slug.
"""

# --- AI FUNCTIE ---
def call_ai(prompt, system_instruction, temp=0.7):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🛡️ Authority Engine v18.0")
st.subheader("Commercial Editorial Style: Geen Slop, Geen Poëzie")

with st.sidebar:
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 1500, 900, step=50)
    
    start_btn = st.button("GENEREER ARTIKEL")

if start_btn:
    with st.status("Artikel wordt gegenereerd...", expanded=True) as status:
        # FASE 1: ARCHITECT
        blueprint = call_ai(f"Plan voor {client_name} op {target_domain}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, url=target_url))
        
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = word_count_target // 4

        # FASE 2: WRITING
        for i, s in enumerate(sections):
            # De link-instructie wordt hier hard in de string gezet
            if i == 0:
                l_inst = f"VERPLICHTE LINK: Verwerk de hyperlink exact zo in de tekst: [{anchor_text}]({target_url})"
            else:
                l_inst = "Gebruik GEEN hyperlinks in deze sectie."

            st.write(f"Sectie {i+1} schrijven...")
            section_text = call_ai(
                f"Hoofdstuk: {s}",
                WRITER_PROMPT.format(section_target=section_target, client=client_name, link_instruction=l_inst),
            )
            full_raw_content += f"\n\n## {section_text}"

        # FASE 3: ASSEMBLER
        st.write("Eindredactie...")
        final_article = call_ai(f"Eindredactie voor:\n{full_raw_content}", 
                                ASSEMBLER_PROMPT.format(target=word_count_target, url=target_url, anchor=anchor_text), temp=0.4)
        
        status.update(label="Artikel voltooid", state="complete")

    # OUTPUT
    st.metric("Aantal woorden", count_words(final_article))
    st.markdown(final_article)
    st.download_button("Download Markdown", final_article, file_name="artikel.md")
