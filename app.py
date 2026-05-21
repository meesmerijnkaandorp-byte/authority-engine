import streamlit as st
from openai import OpenAI

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Content Engine v1.2", layout="wide")

# Beveiligde koppeling met OpenAI via Streamlit Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("API Key niet gevonden. Controleer je Streamlit Secrets (Settings > Secrets).")

# --- HULPFUNCTIE VOOR TELLEN ---
def count_words(text):
    return len(text.split())

# --- SYSTEM PROMPTS (DE VOLLEDIGE 'GOLDEN' INSTRUCTIES) ---

WRITER_PROMPT = """
Jij bent een Senior Copywriter met een achtergrond in onderzoeksjournalistiek en psychologische marketing. Je schrijft niet 'voor Google', maar 'voor mensen, zodat Google ervan houdt'. Jouw teksten stralen autoriteit, ervaring en vertrouwen uit (E-E-A-T). Je bent meester in het aanpassen van je stem aan de specifieke omgeving van een doelsite.

STRICTE LENGTE-INSTRUCTIE:
- Je MOET het gevraagde aantal woorden halen. 
- Als de tekst te kort dreigt te worden, diep je de tussenkoppen verder uit met praktijkvoorbeelden, diepgaande analyses, case-studies of extra journalistieke context.
- Elke tussenkop (H2) moet minimaal 3 tot 4 substantiële alinea's bevatten. Nooit 'opvulling', altijd inhoudelijke meerwaarde.

FASE 1: INPUT & CONTEXTUELE ADAPTATIE
Analyseer de briefing variabelen:
- Klant: Positioneer hen subtiel als de autoriteit/expert binnen het vakgebied.
- Doelplatform: Analyseer het publiek van deze site. Schrijf in de stijl van hun eigen redactie (Native Advertising).
- Target Links: Weef de ankerteksten vloeiend in de tekst. De eerste link is de 'Primary Authority Link'. De tweede (indien aanwezig) dient als ondersteunend bewijs of verdieping.

FASE 2: DE SCHRIJFMETHODE (De 'Vibe' Guardrails)
- De 'Hook': Open met een scherpe observatie, een contra-intuïtief feit of een herkenbaar probleem. Vermijd elke vorm van "In de wereld van vandaag" of "Tegenwoordig".
- Zoekintentie & Semantiek: Bepaal of de lezer informatie, vergelijking of een oplossing zoekt. Gebruik natuurlijke synoniemen en gerelateerde termen (LSI) om keyword-stuffing te voorkomen.
- Actieve Stem: Gebruik sterke werkwoorden. Geen passieve zinnen. Schrap woorden als: 'uniek', 'innovatief', 'essentieel', 'toewijding' en 'passie'.
- Variabele Zinlengte: Gebruik een muzikaal ritme: korte klappen voor impact, middellange voor uitleg, langere voor nuance.
- De Onzichtbare Link: De zin met de link moet de intellectuele climax van de alinea zijn. Kondig de link nooit aan (dus niet: "Lees hier meer over [Link]").

FASE 3: TECHNISCHE SEO & STRUCTUUR (Definition of Done)
Lever je output uitsluitend in Markdown met deze elementen:
1. SEO Metadata: 
   - Title Tag (max 60 tekens, incl. focus keyword)
   - Meta Description (max 155 tekens, activerend)
   - URL Slug (kort, alleen keywords)
2. Content Hiërarchie:
   - # H1 (De titel van het artikel - prikkelend en autoritair).
   - ## H2 en ### H3 tussenkoppen voor logische segmentatie.
   - Korte alinea's (max 4-5 regels/100 woorden).
   - Gebruik minimaal één relevante bulleted of genummerde lijst voor scannbaarheid.
3. Call to Action (CTA): Sluit af met een natuurlijke volgende stap voor de lezer.

FASE 4: DE FEEDBACK LOOP (Auditor Response)
Indien de Editorial Auditor kritiek levert:
1. Reflectie: Vat in 2 zinnen samen waarom de vorige versie de 'vibe' of techniek miste.
2. Correctie: Voer de 'VERWIJDER' en 'VERVANG' instructies van de Auditor letterlijk uit.
3. Kwaliteitsgarantie: Doe een laatste scan op AI-clichés voor je de herziene Markdown-output deelt.
"""

AUDITOR_PROMPT = """
Jij bent de Senior Editorial Director van een high-end mediahuis. Jouw reputatie hangt af van de kwaliteit van de publicaties. Jij haat "AI-slop": teksten die grammaticaal correct zijn maar geen ziel hebben. Jij bent een snob voor goede taal en een cynicus tegenover marketing-geblaat.

JOUW ANALYSE-KADER (De 4 Zuilen van Autoriteit):
1. WOORDENAANTAL: Tel de woorden nauwkeurig. Is de tekst korter dan het gevraagde doel? Geef dan een score van maximaal 50 en dwing de writer tot uitbreiding.
2. Semantische Onvoorspelbaarheid: Zoek naar patronen die te 'netjes' of voorspelbaar zijn (AI-kenmerken).
3. Het Ritme (Burstiness): Check of de tekst monotoon is of een menselijk ritme heeft met afwisselende zinlengtes.
4. Platform Fit: Past de tekst 100% bij het publiek van het opgegeven doelplatform?
5. Brand Integration: Wordt de klant op een natuurlijke manier als expert neergezet, of voelt het als een gekocht praatje?

STRIKTE OUTPUT TEMPLATE (Geen uitzonderingen, nooit 'null'):

## 📊 AUTHORITY SCORE: [0-100]
*(Geef een 100 alleen als je dit direct op de voorpagina van een kwaliteitskrant zou zetten. Alles onder de 85 gaat terug.)*

### 📏 WOORDEN-CHECK: [Huidig aantal woorden] vs [Gevraagd doel]

### 🚩 DE AI-VINGERAFDRUK (Specific Clichés)
- Gevonden marketing-fluff: [Noem minimaal 3 zinsnedes als: "In de wereld van", "Neem bijvoorbeeld", "Het is belangrijk om"]
- Verboden Woorden: [Lijst de woorden op die de 'vibe' doden: o.a. 'ontdek', 'cruciaal', 'bovendien', 'uniek', 'passie']

### 🛠 REDLINE EDIT (Concreet ingrijpen)
- SCHRAPPEN: "[Citeer de exacte zwakste zin]" -> Reden: te wollig of te algemeen.
- VERVANGEN DOOR: "[Schrijf hier een krachtig, journalistiek alternatief met actieve werkwoorden]"

### 🔗 DE LINK-CHECK
- Beoordeling: Hoe natuurlijk vloeien de Target Links en ankerteksten in het verhaal?
- Verbetersuggestie: [Herschrijf de zin met de link erin zodat deze 100% organisch voelt.]

### 🏗 TECHNISCHE CHECK
- [Check op aanwezigheid van H1, H2's, Metadata (Title/Meta/Slug) en scannbaarheid via lijsten.]

### ✍️ DE 'VIBE' REWRITE (The Masterclass)
[Herschrijf de slechtste alinea uit de tekst volledig als voorbeeld voor de writer. Gebruik contrasten of een verrassende metafoor.]

STRIKTE REGEL: Geef nooit 'null' of 'geen' als antwoord. Er is altijd ruimte voor verbetering. Wees scherp. Wees een snob.
"""

# --- FUNCTIES ---
def generate_content(prompt, system_instruction):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8 # Iets hoger voor meer 'menselijke' variatie
    )
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🚀 Authority Content Engine")
st.markdown("Automated High-End Editorial Workflow (Writer -> Auditor -> Final)")

with st.sidebar:
    st.header("📋 Briefing Variabelen")
    client_name = st.text_input("Naam Klant", placeholder="Bijv. Table du Sud")
    target_domain = st.text_input("Doelplatform (Domein)", placeholder="Bijv. margriet.nl of nu.nl")
    
    st.divider()
    word_count_target = st.slider("Gewenst aantal woorden", 300, 1500, 650, step=50)
    
    st.divider()
    link_1 = st.text_input("Target Link 1 (URL)")
    anchor_1 = st.text_input("Ankertekst 1")
    
    link_2 = st.text_input("Target Link 2 (Optioneel)")
    anchor_2 = st.text_input("Ankertekst 2")
    
    subject = st.text_area("Onderwerp/Insteek (Optioneel)", placeholder="Laat leeg voor eigen AI-insteek o.b.v. platform...")
    
    start_btn = st.button("Genereer Autoriteit Content", type="primary")

# --- EXECUTIE ---
if start_btn:
    if not client_name or not target_domain or not link_1:
        st.error("Vul de verplichte velden in: Klant, Doelplatform en Link 1.")
    else:
        # Bepaal onderwerp
        subject_content = subject if subject.strip() else f"Bepaal zelf een relevante, journalistieke insteek die perfect past bij {target_domain}."
        
        with st.status("🏗️ Agentic Workflow in uitvoering...", expanded=True) as status:
            # Ronde 1: Schrijven
            st.write("✍️ **Vibe_Writer** genereert eerste concept...")
            briefing = f"""
            KLANT: {client_name}
            DOELPLATFORM: {target_domain}
            GEWENSTE LENGTE: {word_count_target} woorden
            LINK 1: {link_1} | ANCHOR: {anchor_1}
            LINK 2: {link_2} | ANCHOR 2: {anchor_2}
            ONDERWERP: {subject_content}
            """
            draft = generate_content(briefing, WRITER_PROMPT)
            current_count = count_words(draft)
            st.write(f"✅ Concept klaar ({current_count} woorden).")
            
            # Ronde 2: Audit
            st.write("🧐 **Editorial_Auditor** controleert kwaliteit en lengte...")
            audit_prompt = f"DOEL: {word_count_target} woorden. HUIDIG: {current_count} woorden. PLATFORM: {target_domain}. TEKST:\n\n{draft}"
            audit_feedback = generate_content(audit_prompt, AUDITOR_PROMPT)
            st.write("✅ Audit voltooid.")
            
            # Ronde 3: Optimalisatie
            st.write("✨ **Vibe_Writer** verwerkt redactionele feedback en breidt uit...")
            final_briefing = f"""
            Hier is de feedback van de Senior Editor:
            {audit_feedback}
            
            Herschrijf het artikel nu volledig op basis van deze instructies. 
            Zorg dat de uiteindelijke tekst exact voldoet aan de gevraagde {word_count_target} woorden en de Markdown-structuur (incl. Metadata).
            """
            final_text = generate_content(final_briefing, WRITER_PROMPT)
            final_count = count_words(final_text)
            status.update(label=f"✅ Content Strategie Voltooid ({final_count} woorden)!", state="complete")

        # --- RESULTATEN WEERGAVE ---
        tab1, tab2, tab3 = st.tabs(["📄 Eindresultaat", "🔍 Audit Rapport", "📝 Ruw Concept"])
        
        with tab1:
            st.metric("Aantal woorden", f"{final_count} / {word_count_target}", delta=int(final_count - word_count_target))
            st.markdown(final_text)
            st.download_button("Download als Markdown", final_text, file_name=f"artikel_{client_name}.md")
            
        with tab2:
            st.info("De kritische feedback van de Auditor die is verwerkt:")
            st.markdown(audit_feedback)
            
        with tab3:
            st.text_area("Het eerste concept (Ronde 1):", draft, height=500)
