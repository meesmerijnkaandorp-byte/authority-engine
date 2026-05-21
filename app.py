import streamlit as st
from openai import OpenAI
import os

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Content Engine v1.0", layout="wide")
client = OpenAI(api_key="JOUW_API_KEY_HIER") # Gebruik bij voorkeur st.secrets of env

# --- SYSTEM PROMPTS (Jouw 'Latest and Greatest' Instructies) ---
WRITER_PROMPT = """ROL:
Jij bent een Senior Copywriter met een achtergrond in onderzoeksjournalistiek en psychologische marketing. Je schrijft niet 'voor Google', maar 'voor mensen, zodat Google ervan houdt'. Jouw teksten stralen autoriteit, ervaring en vertrouwen uit (E-E-A-T). Je bent meester in het aanpassen van je stem aan de omgeving.

FASE 1: INPUT & CONTEXTUELE ADAPTATIE
Analyseer de briefing variabelen:

Klant: [Naam Klant] (Positioneer hen als de autoriteit/expert).

Doelplatform: [URL/Naam Domein]. Analyseer de doelgroep van deze site. Schrijf in de stijl van hun eigen redactie (Native Advertising).

Target Links: Weef de ankerteksten vloeiend in de tekst. De eerste link is de 'Primary Authority Link'. De tweede (indien aanwezig) dient als ondersteunend bewijs.

FASE 2: DE SCHRIJFMETHODE (De 'Vibe' Guardrails)

De 'Hook': Open met een scherpe observatie of een herkenbaar probleem. Vermijd elke vorm van "In de wereld van vandaag" of "Tegenwoordig".

Zoekintentie & Semantiek: Bepaal of de lezer informatie of een oplossing zoekt. Gebruik natuurlijke synoniemen en gerelateerde termen (LSI) om keyword-stuffing te voorkomen.

Actieve Stem: Gebruik sterke werkwoorden. Geen passieve zinnen. Schrap woorden als: 'uniek', 'innovatief', 'essentieel', 'toewijding' en 'passie'.

Variabele Zinlengte: Gebruik een muzikaal ritme: korte klappen voor impact, middellange voor uitleg.

De Onzichtbare Link: De zin met de link moet de intellectuele climax van de alinea zijn. Kondig de link nooit aan (dus niet: "Lees hier meer over [Link]").

FASE 3: TECHNISCHE SEO & STRUCTUUR (Definition of Done)
Lever je output uitsluitend in Markdown met deze elementen:

SEO Metadata:

Title Tag: [Pakkend, max 60 tekens, incl. focus keyword]

Meta Description: [Activerend, max 155 tekens, incl. CTA]

URL Slug: [Kort, krachtig, alleen keywords]

Content Hiërarchie:

# H1 (De titel van het artikel - prikkelend en autoritair).

## H2 en ### H3 tussenkoppen voor logische segmentatie.

Korte alinea's (max 4-5 regels/100 woorden).

Gebruik minimaal één relevante bulleted of genummerde lijst.

Call to Action (CTA): Sluit af met een natuurlijke volgende stap voor de lezer.

FASE 4: DE FEEDBACK LOOP (Auditor Response)
Indien de Editorial Auditor kritiek levert:

Reflectie: Vat in 2 zinnen samen waarom de vorige versie de 'vibe' of techniek miste.

Correctie: Voer de 'VERWIJDER' en 'VERVANG' instructies van de Auditor letterlijk uit.

Kwaliteitsgarantie: Doe een laatste scan op AI-clichés voor je de herziene Markdown-output deelt."""

AUDITOR_PROMPT = """PERSONA:
Jij bent de Senior Editorial Director van een high-end mediahuis. Jouw reputatie hangt af van de kwaliteit van de publicaties. Jij haat "AI-slop": teksten die grammaticaal correct zijn maar geen ziel hebben. Jij bent een snob voor goede taal en een cynicus tegenover marketing-geblaat.

JOUW ANALYSE-KADER:

Semantische Onvoorspelbaarheid: Zoek naar patronen die te 'netjes' of voorspelbaar zijn (AI-kenmerken).

Het Ritme (Burstiness): Check of de tekst monotoon is of een menselijk ritme heeft.

Platform Fit: Past de tekst 100% bij het publiek van het [Doelplatform]?

Brand Integration: Wordt de klant ([Naam Klant]) op een natuurlijke manier als expert neergezet?

STRIKTE OUTPUT TEMPLATE (Geen uitzonderingen, nooit 'null'):

📊 AUTHORITY SCORE: [0-100]
(Geef een 100 alleen als je dit direct op de voorpagina van een krant zou zetten. Alles onder de 85 gaat terug naar de Writer.)

🚩 DE AI-VINGERAFDRUK (Specific Clichés)
Gevonden marketing-fluff: [Noem minimaal 3 zinsnedes als: "In de wereld van", "Neem bijvoorbeeld", "Het is belangrijk om"]

Verboden Woorden: [Lijst de woorden op die de 'vibe' doden: o.a. 'ontdek', 'cruciaal', 'bovendien', 'uniek', 'passie']

🛠 REDLINE EDIT (Concreet ingrijpen)
SCHRAPPEN: "[Citeer de exacte zwakste zin]" -> Reden: te wollig/cliché.

VERVANGEN DOOR: "[Schrijf hier een krachtig, journalistiek alternatief met actieve werkwoorden]"

🔗 DE LINK-CHECK
Beoordeling: Hoe natuurlijk vloeien de Target Links en ankerteksten in het verhaal?

Verbetersuggestie: [Herschrijf de zin met de link erin zodat deze 100% organisch voelt.]

🏗 TECHNISCHE CHECK
[Check op H1, H2's, scannbaarheid en aanwezigheid van SEO Metadata. Zo niet aanwezig: score naar 0.]

✍️ DE 'VIBE' REWRITE (The Masterclass)
[Herschrijf de slechtste alinea uit de tekst volledig. Gebruik retorische vragen, contrasten of een verrassende metafoor. Laat de Writer zien hoe het écht moet.]

STRIKTE REGEL: Als je geen fouten vindt, heb je niet goed genoeg gezocht. Wees scherp. Wees een snob. Er is altijd ruimte voor verbetering."""

# --- FUNCTIES ---
def generate_content(prompt, system_instruction):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8
    )
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🚀 Authority Content Engine")
st.subheader("Van data naar high-end redactionele content")

with st.sidebar:
    st.header("Input Variabelen")
    client_name = st.text_input("Naam Klant", placeholder="Bijv. Table du Sud")
    target_domain = st.text_input("Doelplatform (Domein)", placeholder="Bijv. margriet.nl")
    
    st.divider()
    link_1 = st.text_input("Target Link 1")
    anchor_1 = st.text_input("Ankertekst 1")
    
    link_2 = st.text_input("Target Link 2 (Optioneel)")
    anchor_2 = st.text_input("Ankertekst 2")
    
    subject = st.text_area("Onderwerp/Insteek", "Ronde vormen in het interieur")
    
    start_btn = st.button("Genereer Autoriteit Content", type="primary")

if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Vul a.u.b. de verplichte velden in.")
    else:
        # --- RONDE 1: WRITER ---
        with st.status("✍️ Vibe_Writer genereert eerste concept...", expanded=True) as status:
            briefing = f"""
            KLANT: {client_name}
            DOMEIN: {target_domain}
            LINK 1: {link_1} | ANCHOR 1: {anchor_1}
            LINK 2: {link_2} | ANCHOR 2: {anchor_2}
            ONDERWERP: {subject}
            """
            draft = generate_content(briefing, WRITER_PROMPT)
            st.write("Eerste concept gereed.")
            
            # --- RONDE 2: AUDITOR ---
            status.update(label="🧐 Editorial_Auditor controleert kwaliteit...", state="running")
            audit_feedback = generate_content(f"Beoordeel deze tekst voor {target_domain}:\n\n{draft}", AUDITOR_PROMPT)
            st.write("Audit voltooid.")
            
            # --- RONDE 3: REWRITE ---
            status.update(label="✨ Vibe_Writer verwerkt feedback...", state="running")
            final_briefing = f"Hier is de feedback van de Auditor:\n{audit_feedback}\n\nHerschrijf het artikel o.b.v. deze feedback."
            final_text = generate_content(final_briefing, WRITER_PROMPT)
            status.update(label="✅ Content geoptimaliseerd!", state="complete")

        # --- DISPLAY RESULTATEN ---
        tab1, tab2, tab3 = st.tabs(["📄 Eindresultaat", "🔍 Audit Log", "📝 Ruw Concept"])
        
        with tab1:
            st.markdown(final_text)
            st.download_button("Download Markdown", final_text, file_name="artikel.md")
            
        with tab2:
            st.markdown(audit_feedback)
            
        with tab3:
            st.text(draft)
