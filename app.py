import streamlit as st
from openai import OpenAI

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Content Engine v1.0", layout="wide")

# Beveiligde koppeling met je OpenAI Key uit Streamlit Secrets
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("API Key niet gevonden of onjuist. Controleer je Streamlit Secrets.")

# --- SYSTEM PROMPTS (V9 Master Versies) ---

WRITER_PROMPT = """
Jij bent een Senior Copywriter met een achtergrond in onderzoeksjournalistiek en psychologische marketing. Je schrijft niet 'voor Google', maar 'voor mensen, zodat Google ervan houdt'. Jouw teksten stralen autoriteit, ervaring en vertrouwen uit (E-E-A-T). Je bent meester in het aanpassen van je stem aan de omgeving.

FASE 1: INPUT & CONTEXTUELE ADAPTATIE
Analyseer de briefing variabelen:
- Klant: Positioneer hen als de autoriteit/expert.
- Doelplatform: Analyseer de doelgroep van deze site. Schrijf in de stijl van hun eigen redactie (Native Advertising).
- Target Links: Weef de ankerteksten vloeiend in de tekst. De eerste link is de 'Primary Authority Link'. De tweede (indien aanwezig) dient als ondersteunend bewijs.

FASE 2: DE SCHRIJFMETHODE (De 'Vibe' Guardrails)
- De 'Hook': Open met een scherpe observatie of een herkenbaar probleem. Vermijd elke vorm van "In de wereld van vandaag" of "Tegenwoordig".
- Zoekintentie & Semantiek: Bepaal of de lezer informatie of een oplossing zoekt. Gebruik natuurlijke synoniemen en gerelateerde termen (LSI).
- Actieve Stem: Gebruik sterke werkwoorden. Geen passieve zinnen. Schrap woorden als: 'uniek', 'innovatief', 'essentieel', 'toewijding' en 'passie'.
- Variabele Zinlengte: Gebruik een muzikaal ritme: korte klappen voor impact, middellange voor uitleg.
- De Onzichtbare Link: De zin met de link moet de intellectuele climax van de alinea zijn. Kondig de link nooit aan.

FASE 3: TECHNISCHE SEO & STRUCTUUR (Definition of Done)
Lever je output uitsluitend in Markdown met deze elementen:
1. SEO Metadata: Title Tag (max 60 tekens), Meta Description (max 155 tekens), URL Slug.
2. Content Hiërarchie: # H1 titel, ## H2 en ### H3 tussenkoppen.
3. Scannbaarheid: Korte alinea's (max 100 woorden) en minimaal één lijst (bullet points).
4. Call to Action (CTA): Sluit af met een natuurlijke volgende stap voor de lezer.

FASE 4: DE FEEDBACK LOOP (Auditor Response)
Indien de Editorial Auditor kritiek levert:
1. Reflectie: Vat in 2 zinnen samen waarom de vorige versie de 'vibe' of techniek miste.
2. Correctie: Voer de 'VERWIJDER' en 'VERVANG' instructies van de Auditor letterlijk uit.
3. Kwaliteitsgarantie: Doe een laatste scan op AI-clichés voor je de herziene Markdown-output deelt.
"""

AUDITOR_PROMPT = """
Jij bent de Senior Editorial Director van een high-end mediahuis. Jouw reputatie hangt af van de kwaliteit van de publicaties. Jij haat "AI-slop": teksten die grammaticaal correct zijn maar geen ziel hebben. Jij bent een snob voor goede taal en een cynicus tegenover marketing-geblaat.

JOUW ANALYSE-KADER:
1. Semantische Onvoorspelbaarheid: Zoek naar patronen die te 'netjes' of voorspelbaar zijn.
2. Het Ritme (Burstiness): Check of de tekst monotoon is of een menselijk ritme heeft.
3. Platform Fit: Past de tekst 100% bij het publiek van het opgegeven doelplatform?
4. Brand Integration: Wordt de klant op een natuurlijke manier als expert neergezet?

STRIKTE OUTPUT TEMPLATE (Geen uitzonderingen, nooit 'null'):

## 📊 AUTHORITY SCORE: [0-100]
(Geef een 100 alleen als je dit direct op de voorpagina van een krant zou zetten. Alles onder de 85 gaat terug naar de Writer.)

### 🚩 DE AI-VINGERAFDRUK (Specific Clichés)
- Gevonden marketing-fluff: [Noem minimaal 3 zinsnedes]
- Verboden Woorden: [Lijst de woorden op: o.a. 'ontdek', 'cruciaal', 'bovendien', 'uniek']

### 🛠 REDLINE EDIT (Concreet ingrijpen)
- SCHRAPPEN: "[Citeer exacte zin]" -> Reden: te wollig.
- VERVANGEN DOOR: "[Krachtig, journalistiek alternatief]"

### 🔗 DE LINK-CHECK
- Beoordeling: Hoe natuurlijk vloeien de Target Links in het verhaal?
- Verbetersuggestie: [Herschrijf de zin met de link erin organisch.]

### 🏗 TECHNISCHE CHECK
- [Check op H1, H2's, Metadata en scannbaarheid. Indien fout: score 0.]

### ✍️ DE 'VIBE' REWRITE (The Masterclass)
[Herschrijf de slechtste alinea volledig als voorbeeld voor de writer.]

STRIKTE REGEL: Geef nooit 'null' of 'geen' als antwoord. Er is altijd ruimte voor verbetering.
"""

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
st.markdown("Genereer high-end redactionele content met een automatische editorial loop.")

with st.sidebar:
    st.header("📋 Briefing Variabelen")
    client_name = st.text_input("Naam Klant", placeholder="Bijv. Table du Sud")
    target_domain = st.text_input("Doelplatform (Domein)", placeholder="Bijv. margriet.nl of nu.nl")
    
    st.divider()
    word_count = st.slider("Gewenst aantal woorden", 300, 1500, 600, step=50)
    
    st.divider()
    link_1 = st.text_input("Target Link 1 (URL)")
    anchor_1 = st.text_input("Ankertekst 1")
    
    link_2 = st.text_input("Target Link 2 (Optioneel)")
    anchor_2 = st.text_input("Ankertekst 2")
    
    subject = st.text_area("Onderwerp/Insteek", placeholder="Waar moet het artikel over gaan?")
    
    start_btn = st.button("Genereer Autoriteit Content", type="primary")

# --- EXECUTIE ---
if start_btn:
    if not client_name or not target_domain or not link_1 or not subject:
        st.error("Vul alle verplichte velden in (Klant, Domein, Link 1 en Onderwerp).")
    else:
        # Ronde 1: Eerste Concept
        with st.status("🏗️ Agentic Workflow in uitvoering...", expanded=True) as status:
            st.write("✍️ **Vibe_Writer** genereert eerste concept...")
            briefing = f"""
            KLANT: {client_name}
            DOELPLATFORM: {target_domain}
            GEWENSTE LENGTE: {word_count} woorden
            LINK 1: {link_1} | ANKER: {anchor_1}
            LINK 2: {link_2} | ANCHOR 2: {anchor_2}
            ONDERWERP: {subject}
            """
            draft = generate_content(briefing, WRITER_PROMPT)
            st.write("✅ Eerste concept gereed.")
            
            # Ronde 2: Audit
            st.write("🧐 **Editorial_Auditor** controleert kwaliteit en E-E-A-T...")
            audit_prompt = f"Beoordeel deze tekst geschreven voor {target_domain} (doel: {word_count} woorden):\n\n{draft}"
            audit_feedback = generate_content(audit_prompt, AUDITOR_PROMPT)
            st.write("✅ Audit voltooid.")
            
            # Ronde 3: Optimalisatie
            st.write("✨ **Vibe_Writer** verwerkt redactionele feedback...")
            final_briefing = f"""
            Hier is de feedback van de Senior Editor:
            {audit_feedback}
            
            Herschrijf het artikel nu volledig op basis van deze instructies. 
            Zorg dat de uiteindelijke tekst exact voldoet aan de gevraagde {word_count} woorden en de Markdown-structuur.
            """
            final_text = generate_content(final_briefing, WRITER_PROMPT)
            status.update(label="✅ Content Strategie Voltooid!", state="complete")

        # --- RESULTATEN WEERGAVE ---
        tab1, tab2, tab3 = st.tabs(["📄 Eindresultaat", "🔍 Audit Rapport", "📝 Ruw Concept"])
        
        with tab1:
            st.success(f"Artikel geoptimaliseerd voor {target_domain}")
            st.markdown(final_text)
            st.download_button("Download als Markdown", final_text, file_name=f"artikel_{client_name}.md")
            
        with tab2:
            st.info("De kritische feedback van de Auditor die is verwerkt in de definitieve versie:")
            st.markdown(audit_feedback)
            
        with tab3:
            st.text_area("Het eerste concept (vóór feedback):", draft, height=400)
