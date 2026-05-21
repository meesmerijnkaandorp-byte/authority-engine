import streamlit as st
from openai import OpenAI
import time

# --- PRODUCT CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v3.0 | Human-Grade", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt.")

def count_words(text):
    return len(text.split())

# --- FASE 1: DE ARCHITECT (Gedetailleerde Bouwtekening) ---
ARCHITECT_PROMPT = """Jij bent de Hoofdredacteur van een kwaliteitsmagazine. 
Jouw taak is om een artikel-structuur uit te zetten voor een tekst van {target} woorden.
ONDERWERP: {subject}
KLANT: {client}
PLATFORM: {platform}

EISEN:
1. Maak exact 4 hoofdstukken (H2).
2. Per hoofdstuk geef je 3 'Diepgang-punten' die de schrijver MOET uitwerken.
3. De insteek moet menselijk en observerend zijn (denk aan 'zaterdagmorgen-energie').
4. ALLES IN HET NEDERLANDS. Geen Engelse termen in de titels.
"""

# --- FASE 2: DE ELITE WRITER (Sectie-voor-Sectie) ---
WRITER_PROMPT = """Jij bent een freelance journalist voor bladen als Linda.man of Quote. 
Jouw stijl is observerend, menselijk en wars van marketing-clichés. 

GEBRUIK DE 'SHOW, DON'T TELL' METHODE:
- Schrijf niet: "Het is efficiënt." 
- Schrijf: "Alles past in één keer achter de deuren van de laadruimte, zonder dat je drie keer op en neer hoeft te rijden."

STRICTE EISEN:
1. TAAL: Uitsluitend Nederlands. Gebruik GEEN Engelse leenwoorden of constructies zoals 'de beginnings'.
2. LENGTE: Schrijf voor deze specifieke sectie minimaal {section_target} woorden.
3. FLOW: Begin direct met de inhoud. Geen introducties zoals "In deze sectie gaan we kijken naar...".
4. BRANDING: De klant ({client}) en de links ({link1}, {link2}) moeten aanvoelen als gereedschap voor de lezer, niet als een advertentie.
"""

# --- FASE 3: DE POLISHER (Narratieve Lijm) ---
POLISHER_PROMPT = """Jij bent een meester-redacteur. Je krijgt 4 losse hoofdstukken. 
Smeed ze aaneen tot één vloeiend essay van topniveau.
- Verwijder dubbelingen.
- Zorg dat de overgangen tussen hoofdstukken natuurlijk voelen.
- Voeg SEO-metadata (Title, Meta, Slug) toe aan de top.
- Controleer op 'AI-isme' (woorden als 'daarnaast', 'bovendien', 'cruciaal') en vervang ze door menselijke taal.
"""

# --- ENGINE FUNCTIE ---
def call_ai(prompt, system_instruction):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🛡️ Authority Engine v3.0")
st.subheader("Human-Centric Content Pipeline")

with st.sidebar:
    st.header("Briefing")
    client_name = st.text_input("Klant", value="Avis")
    target_domain = st.text_input("Platform", value="Lifestyle Blog")
    word_count_target = st.slider("Target Woorden", 600, 1500, 900, step=100)
    
    st.divider()
    link_1 = st.text_input("URL 1")
    anchor_1 = st.text_input("Anchor 1")
    link_2 = st.text_input("URL 2 (Optioneel)")
    anchor_2 = st.text_input("Anchor 2")
    
    subject = st.text_area("Insteek", value="De psychologie van verhuizen en de drang naar een frisse start.")
    start_btn = st.button("GENEREER MEESTERWERK", type="primary")

if start_btn:
    with st.status("🚀 Productie gestart...", expanded=True) as status:
        # STAP 1: ARCHITECTUUR
        st.write("📐 Architect ontwerpt de diepgang...")
        blueprint = call_ai(f"Insteek: {subject}", ARCHITECT_PROMPT.format(target=word_count_target, subject=subject, client=client_name, platform=target_domain))
        
        # STAP 2: SECTIE SCHRIJVEN
        st.write("🖋️ Elite Writer start de hoofdstukken...")
        h2_sections = blueprint.split("##")[1:]
        full_content = ""
        section_target = (word_count_target // 4) + 50 # Forceer over-lengte
        
        for i, s in enumerate(h2_sections):
            st.write(f"  - Schrijven hoofdstuk {i+1}...")
            section_text = call_ai(
                f"Sectie Instructie: {s}\nLinks: {link_1} ({anchor_1}), {link_2} ({anchor_2})",
                WRITER_PROMPT.format(section_target=section_target, client=client_name, link1=link_1, link2=link_2)
            )
            full_content += f"\n\n## {section_text}"
            time.sleep(0.5)

        # STAP 3: POLISH
        st.write("✨ Eindredactie smeedt het verhaal aaneen...")
        final_article = call_ai(f"Hier is de ruwe content:\n{full_content}", POLISHER_PROMPT)
        
        status.update(label="✅ Content klaar voor publicatie", state="complete")

    # OUTPUT
    final_count = count_words(final_article)
    st.metric("Eindresultaat", f"{final_count} woorden", delta=int(final_count - word_count_target))
    
    tab1, tab2 = st.tabs(["📄 Final Asset", "🧬 Blueprint"])
    with tab1:
        st.markdown(final_article)
        st.download_button("Download Markdown", final_article, file_name="artikel.md")
    with tab2:
        st.markdown(blueprint)
