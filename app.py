import streamlit as st
from openai import OpenAI

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Content Engine v1.3 | ZERO-TRACE", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("API Key niet gevonden. Controleer je Streamlit Secrets.")

def count_words(text):
    return len(text.split())

# --- SYSTEM PROMPTS (V13 - THE TITAN UPDATE) ---

WRITER_PROMPT = """
Jij bent een wereldklasse essayist en onderzoeksjournalist voor bladen als The New Yorker of Wired. Jouw teksten zijn onmogelijk te onderscheiden van menselijk werk omdat je 'grillig' schrijft: je varieert extreem in zinsbouw, gebruikt subtiele humor, en bouwt complexe argumenten op die AI normaal gesproken overslaat.

STRICTE OPDRACHT:
1. WOORDENAANTAL IS HEILIG: Als er 800 woorden gevraagd worden, lever je er minimaal 805. Nooit minder.
2. ANTI-AI SCHRIJFSTIJL: Gebruik 'low-frequency' woorden (geen clichés). Gebruik af en toe een retorische vraag, een krachtige metafoor of een persoonlijke anekdote.
3. DIEPGANG: In plaats van feiten op te sommen, leg je de 'waarom' en 'hoe' uit. Graaf dieper in de materie.
4. STRUCTUUR: Elke H2-sectie MOET bestaan uit minimaal 4 alinea's met elk een eigen sub-focus.

FASE 1: CONTEXT & E-E-A-T
- Klant: Positioneer hen als dé autoriteit.
- Platform: Kopieer de 'vibe' van de doelsite perfect.
- Links: De links moeten zo organisch staan dat een lezer denkt dat jij ze zelf hebt uitgekozen als referentiemateriaal.

FASE 2: DEFINITION OF DONE (Markdown)
- SEO Metadata (Title, Meta, Slug) bovenaan.
- # H1 Titel die nieuwsgierigheid opwekt.
- ## H2 en ### H3 koppen voor diepe segmentatie.
- Minimaal één lijst (bullets/genummerd).
- CTA die de lezer echt aan het denken zet.

BIJ FEEDBACK:
- De Auditor is jouw vijand. Bewijs dat hij ongelijk heeft door de tekst nog menselijker, langer en scherper te maken.
"""

AUDITOR_PROMPT = """
Jij bent de meest gevreesde hoofdredacteur in de journalistiek. Jij hebt een neus voor AI en je haat het. Jouw doel is om elke tekst die 'vlak' aanvoelt te vernietigen.

JOUW STRIKTE PROTOCOL:
1. WOORDEN-DICTATUUR: Is de tekst 1 woord te kort? SCORE = 0. Wees meedogenloos.
2. AI-DETECTIE: Zoek naar 'voorspelbaarheid'. Als zinnen allemaal dezelfde lengte hebben of beginnen met 'Daarnaast' of 'Bovendien', keur je het af.
3. INHOUD: Is het een oppervlakkig marketingpraatje? Zo ja: Score < 40.
4. LINK-INTEGRATIE: Als de link eruitziet als linkbuilding, heb je gefaald.

STRIKTE OUTPUT TEMPLATE (VERPLICHT):

## 📊 AUTHORITY SCORE: [0-100]
### 📏 WOORDEN-CHECK: [Aantal] vs [Doel] -> [STATUS: GOEDGEKEURD/AFGEKEURD]

### 🚩 AI-VINGERAFDRUK & CLICHÉS
- [Lijst van minimaal 5 punten waar de tekst te robotachtig is]

### 🛠 DE 'SLAGER' EDIT (Wat moet weg/anders)
- VERWIJDER: "[Zin]" -> Reden: "Dit is luie AI-tekst."
- VERVANG DOOR: "[Geef hier een complexe, menselijke variant]"

### 🔗 LINK-NATURALITEIT
- [Beoordeling van de integratie]

### ✍️ MASTERCLASS REWRITE
[Herschrijf de zwakste sectie op een manier die een Pulitzer-prijs waardig is. Laat de Writer zien hoe diep hij moet gaan.]

STRIKTE REGEL: Je bent NOOIT tevreden. Er is altijd een 85+ score nodig voor doorvoer.
"""

# --- FUNCTIES ---
def generate_content(prompt, system_instruction):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.85 # Hoger voor meer burstiness en minder voorspelbaarheid
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🛡️ Zero-Trace Authority Engine")
st.markdown("Geoptimaliseerd voor 2026: Ongeëvenaarde kwaliteit zonder AI-voetafdruk.")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", placeholder="Bijv. Table du Sud")
    target_domain = st.text_input("Platform", placeholder="Bijv. ad.nl")
    
    st.divider()
    word_count_target = st.slider("Target Woorden", 300, 1500, 800, step=50)
    
    st.divider()
    link_1 = st.text_input("Link 1 (URL)")
    anchor_1 = st.text_input("Anchor 1")
    link_2 = st.text_input("Link 2 (Optioneel)")
    anchor_2 = st.text_input("Anchor 2")
    
    subject = st.text_area("Insteek (Optioneel)", placeholder="Leeglaten voor AI-creativiteit...")
    
    start_btn = st.button("RUN AGENTIC LOOP", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Verplichte velden missen.")
    else:
        subject_content = subject if subject.strip() else f"Schrijf een diepgaand, menselijk artikel voor {target_domain} waarbij {client_name} als dé autoriteit wordt neergezet."
        
        with st.status("🚀 Systeem voert Zero-Trace protocol uit...", expanded=True) as status:
            # RONDE 1
            st.write("🖋️ **Titan_Writer** bouwt fundament...")
            briefing = f"KLANT: {client_name}\nPLATFORM: {target_domain}\nDOEL: {word_count_target} woorden\nLINK: {link_1} ({anchor_1})\nONDERWERP: {subject_content}"
            draft = generate_content(briefing, WRITER_PROMPT)
            c1 = count_words(draft)
            
            # RONDE 2
            st.write(f"🧐 **Inquisitor_Auditor** fileert concept ({c1} woorden)...")
            audit_feedback = generate_content(f"DOEL: {word_count_target}. HUIDIG: {c1}. TEKST:\n\n{draft}", AUDITOR_PROMPT)
            
            # RONDE 3
            st.write("✨ **Titan_Writer** voert finale optimalisatie uit...")
            final_briefing = f"DE EDITOR HEEFT JE TEKST AFGEKEURD. VERWERK DIT:\n{audit_feedback}\n\nEis: EXACT {word_count_target} woorden of meer. Geen excuses."
            final_text = generate_content(final_briefing, WRITER_PROMPT)
            c_final = count_words(final_text)
            
            status.update(label=f"✅ Protocol voltooid: {c_final} woorden.", state="complete")

        t1, t2, t3 = st.tabs(["📄 Publicatie", "🔍 Audit", "📝 Log"])
        with t1:
            st.metric("Kwaliteits-check", f"{c_final} woorden", delta=int(c_final - word_count_target))
            st.markdown(final_text)
            st.download_button("Download Markdown", final_text, file_name="high_end_content.md")
        with t2:
            st.markdown(audit_feedback)
        with t3:
            st.text_area("Draft V1", draft, height=400)
