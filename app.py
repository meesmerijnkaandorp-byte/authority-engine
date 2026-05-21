import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v13.0 | The Texture Engine", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt in Secrets.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (Narratieve Conflict Planner) ---
ARCHITECT_PROMPT = """Jij bent de Redactiechef van een nuchter opinieblad. Ontwerp een blueprint voor een essay van {target} woorden.
URL: {url} | KLANT: {client}

JOUW OPDRACHT:
1. GEEN HANDLEIDING: Plan geen tekst over 'hoe kies je een kast'. Plan een tekst over de REALITEIT van ruimtegebrek en de logica van bezit.
2. CONFLICT: Elke H2-sectie moet een menselijke frustratie of observatie als basis hebben (bijv. de 'stoel met kleding', de weigerende lade, de gedeelde slaapkamer).
3. STRUCTUUR: Exact 4 hoofdstukken (H2).
4. GEEN CLICHÉS: Verbied expliciet de woorden: esthetiek, essentieel, oase, harmonie, balans.
"""

# --- AGENT 2: THE TITAN WRITER (De 'Texture' Schrijver) ---
WRITER_PROMPT = """Jij bent een nuchtere, scherpe journalist. Je schrijft voor een publiek dat allergisch is voor marketing-gezwets.

JOUW IDENTITEIT:
- Je schrijft met 'textuur'. Je benoemt details: de inbussleutel die net niet past, de geur van nieuw spaanplaat, het gewicht van een winterjas op een doorbuigende roede.
- GEEN MOOIPRATERIJ: Woorden als 'oase', 'esthetiek', 'harmonieus', 'meubelstuk', 'tal van', 'ontdek' en 'essentieel' resulteren in ontslag.
- ZINSBOUW: Schrijf zoals een mens praat: direct, soms kort, soms een diepe observatie.

{link_instruction}

DOEL: Schrijf exact {section_target} woorden voor dit hoofdstuk. Graaf dieper in de modder, vlieg niet over de oppervlakte.
{feedback_instruction}
"""

# --- AGENT 3: THE ASSEMBLER (De Narratieve Slijper) ---
ASSEMBLER_PROMPT = """Jij bent een meedogenloze Eindredacteur. Smeed de teksten aaneen tot een essay van {target} woorden.

JOUW TAKEN:
1. LINK-ENFORCEMENT: Er mag in de gehele tekst slechts ÉÉN hyperlink staan: [{anchor}]({url}). Als je een tweede ziet: vernietig de link en maak er platte tekst van.
2. SLOP-SNOEIER: Verwijder elke zin die klinkt als 'algemeen advies'. Vervang algemene termen door specifieke observaties.
3. VOLUME-PRECISIE: Trim de tekst naar maximaal {target} woorden. Verwijder 'wolligheid'.
4. SEO: Metadata (Title, Meta, Slug) moet feitelijk en direct zijn. Geen 'Ontdek...' titels.
"""

# --- AGENT 4: THE GATEKEEPER (De Slop-Meter) ---
SCORER_PROMPT = """Jij bent een AI-detectie expert. Beoordeel de tekst op 'menselijke textuur' en technische eisen.
SCORE < 10 ALS:
- De link [{anchor}]({url}) ontbreekt.
- De tekst woorden bevat als: oase, esthetiek, harmonieus, essentieel, tal van.
- De tekst leest als een handleiding ("Stap 1, Stap 2").
- De tekst meer dan 10% afwijkt van {target} woorden.

JSON OUTPUT:
{{
    "score": 0,
    "reasoning": "Wees brutaal. Waar ruikt de tekst nog naar een chatbot?",
    "link_ok": true/false,
    "forbidden_words_found": ["lijst"]
}}
"""

# --- AI ENGINE ---
def call_ai(prompt, system_instruction, temp=0.85):
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
st.title("🛡️ Authority Engine v13.0")
st.subheader("The Texture Engine: Zero-Slop & Narrative Depth")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("Target URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 1500, 900, step=50)
    
    start_btn = st.button("PRODUCEER NARRATIEF ASSET", type="primary")

if start_btn:
    with st.status("🏗️ Narratieve pijplijn geactiveerd...", expanded=True) as status:
        # FASE 1: ARCHITECT
        st.write("📐 Architectuur ontwerpen (Texture mapping)...")
        blueprint = call_ai(f"Insteek voor {target_url} op {target_domain}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain, url=target_url))
        
        # FASE 2: SEQUENTIAL WRITING
        h2_sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int((word_count_target * 1.05) // 4) # Kleine buffer
        
        for i, s in enumerate(h2_sections):
            # Link alleen in de eerste sectie doorgeven
            if i == 0:
                l_inst = f"TECHNISCH BEVEL: Verwerk exact één keer de Markdown link: [{anchor_text}]({target_url})."
            else:
                l_inst = "GEBRUIK GEEN HYPERLINKS. Schrijf uitsluitend platte tekst."
            
            st.write(f"  🖋️ Schrijven sectie {i+1}...")
            section_text = call_ai(
                f"Sectie Instructie: {s}",
                WRITER_PROMPT.format(section_target=section_target, client=client_name, link_instruction=l_inst, feedback_instruction=""),
            )
            full_raw_content += f"\n\n## {section_text}"

        # FASE 3: ASSEMBLY
        st.write("  ✨ Assembleren en 'slop' verwijderen...")
        final_article = call_ai(f"Smeed aaneen tot {word_count_target} woorden. Zorg voor de link [{anchor_text}]({target_url}):\n{full_raw_content}", 
                                ASSEMBLER_PROMPT.format(target=word_count_target, url=target_url, anchor=anchor_text), temp=0.6)
        
        # FASE 4: SCORE
        st.write("  🧐 Kwaliteits-audit door Gatekeeper...")
        score_raw = call_ai(
            f"Beoordeel deze tekst op target {word_count_target}:\n\n{final_article}", 
            SCORER_PROMPT.format(target=word_count_target, anchor=anchor_text, url=target_url), 
            temp=0.1
        )
        # Veiligere JSON extractie
        try:
            score_json = re.search(r'\{.*\}', score_raw, re.DOTALL).group()
            score_data = json.loads(score_json)
        except:
            score_data = {"score": 50, "reasoning": "Scoring failed", "link_ok": False}
        
        final_score = score_data.get("score", 0)
        
        if final_score >= 85:
            status.update(label=f"✅ Asset Gereed (Score: {final_score})", state="complete")
        else:
            status.update(label=f"⚠️ Kwaliteit Onvoldoende (Score: {final_score})", state="error")

    # --- OUTPUT ---
    tab1, tab2 = st.tabs(["📄 Final Asset", "📊 Audit Log"])
    with tab1:
        c_final = count_words(final_article)
        st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
        if final_score < 85:
            st.error(f"Audit mislukt: {score_data.get('reasoning')}")
        st.markdown(final_article)
        st.download_button("Download", final_article, file_name="export.md")
    with tab2:
        st.json(score_data)
        st.text_area("Blueprint", blueprint)
