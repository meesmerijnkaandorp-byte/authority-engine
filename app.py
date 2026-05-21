import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v22.1 | Scope Fix", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("API-sleutel niet gevonden in Secrets.")

def count_words(text):
    return len(text.split())

# --- REDACTIONELE RICHTLIJNEN (Statische strings zonder f-prefix om NameErrors te voorkomen) ---
EDITORIAL_STANCE = """
- STIJL: Lifestyle-journalistiek (Denk aan: Kassa, Radar, of de weekendbijlage van een krant). 
- TOON: Direct, nuchter, adviserend zonder 'vriendelijk' te zijn. 
- GEEN POËZIE: Geen metaforen over dansende kasten of stomme reuzen. 
- FOCUS: De logistiek van het wonen. De keuze voor materialen. De prijs-kwaliteitverhouding van {client}.
- VERBODEN: oase, harmonie, samenspel, ontdek, essentieel, cruciaal, wereld van verschil, baken, feniks, horizon, prachtig, uniek, krachtig, beleving, partner, de tand des tijds.
"""

ARCHITECT_PROMPT = """Jij bent een Content Director. Ontwerp een essay-structuur voor {target} woorden over {url}.
{stance}

STRICTE OPDRACHT:
1. Plan 4 H2-hoofdstukken over: 
   - De frustratie van ruimtegebrek in de Randstad/gemiddeld huis.
   - De technische keuze: schuifdeur vs. draaideur (praktische logica).
   - Materiaalkennis: MDF, spaanplaat, massief hout. Wat koop je voor welk budget?
   - Logistiek: Van bestelling bij {client} naar een gemonteerde kast.
"""

WRITER_PROMPT = """Jij bent een nuchtere consumentenjournalist. Je schrijft voor {platform}.

{stance}

JOUW OPDRACHT:
- Schrijf hoofdstuk {n}. 
- Gebruik concrete details: afmetingen, schroeven, inbussleutels, het gewicht van een jas, de vierkante meterprijs van een slaapkamer.
- EIS: Schrijf minimaal {section_target} woorden. Gebruik GEEN inleidingen.
- ANKER-CHECK: Gebruik het woord '{anchor}' minimaal 2 keer in deze tekst.
"""

ASSEMBLER_PROMPT = """Jij bent de Hoofdredacteur. 
1. Verwijder elke zin die te 'mooi' of 'literair' is. Maak het nuchter.
2. Zorg dat de overgangen tussen de hoofdstukken zakelijk zijn.
3. Check het volume: we mikken op {target} woorden.
4. Genereer Metadata: Title (direct), Meta (informatief), Slug.
"""

# --- AI ENGINE ---
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

# --- UI ---
st.title("🛡️ Authority Engine v22.1")
st.subheader("Commercial Editorial Standard | Stability Update")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("Target URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 1500, 950, step=50)
    
    start_btn = st.button("PRODUCEER ASSET", type="primary")

if start_btn:
    start_time = time.time()
    with st.status("🏗️ Productie in uitvoering...", expanded=True) as status:
        
        # FASE 1: ARCHITECT (Render prompt met variabelen)
        st.write("📐 Architectuur vergrendelen...")
        architect_sys = ARCHITECT_PROMPT.format(
            target=word_count_target, 
            url=target_url, 
            client=client_name, 
            stance=EDITORIAL_STANCE.format(client=client_name)
        )
        blueprint = call_ai(f"Plan voor {target_url}", architect_sys)
        
        # FASE 2: WRITING
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int((word_count_target // 4) + 100)
        
        for i, s in enumerate(sections):
            st.write(f"🖋️ Journalist schrijft Hoofdstuk {i+1}...")
            
            # Render writer prompt
            writer_sys = WRITER_PROMPT.format(
                platform=target_domain,
                stance=EDITORIAL_STANCE.format(client=client_name),
                n=i+1,
                section_target=section_target,
                anchor=anchor_text
            )
            
            section_text = call_ai(f"H2 Sectie: {s}", writer_sys)
            full_raw_content += f"\n\n## {section_text}"

        # FASE 3: ASSEMBLY
        st.write("✨ Eindredactie...")
        assembler_sys = ASSEMBLER_PROMPT.format(target=word_count_target)
        final_article = call_ai(f"Assemblage van:\n{full_raw_content}", assembler_sys, temp=0.4)
        
        # FASE 4: PYTHON TECHNICAL LINK INJECTION
        pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
        final_article = pattern.sub(f"[{anchor_text}]({target_url})", final_article, count=1)

        status.update(label=f"✅ Gereed in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    c_final = count_words(final_article)
    st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
    st.markdown(final_article)
    st.download_button("Download", final_article, file_name="asset.md")
