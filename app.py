import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE & SETUP ---
st.set_page_config(page_title="Authority Engine v21.0 | Final Sentinel", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: OpenAI API-sleutel ontbreekt in Secrets.")

def count_words(text):
    return len(text.split())

# --- DE REDACTIONELE WET (V21.0) ---
BLACK_LIST = [
    "oase", "harmonie", "samenspel", "ontdek", "essentieel", "cruciaal", "wereld van verschil", 
    "baken", "feniks", "horizon", "prachtig", "uniek", "krachtig", "navigeren", "beleving", 
    "perfect", "optimaal", "partner", "tand des tijds", "geoliede machine", "paradigma",
    "het draait allemaal om", "in deze moderne tijd", "belangrijk om te onthouden"
]

GOLDEN_EXAMPLE = """
"Er is een specifiek soort zaterdagmorgen-energie die alleen ontstaat wanneer je de knoop doorhakt: die overvolle berging gaat leeg, die vintage designkast komt er eindelijk... Het passen en meten met een openstaande achterklep en drie spanbanden voelt niet langer als een ludiek avontuur, maar als onnodige stress."
"""

# --- AGENT PROMPTS ---

ARCHITECT_PROMPT = f"""Jij bent de Lead Strategist. Ontwerp een blueprint voor {{target}} woorden over {{url}}.
STYLE: Gebruik de nuchtere, observerende toon van: "{GOLDEN_EXAMPLE}"

EISEN:
1. Plan 4 H2-hoofdstukken gebaseerd op 'frictie' en 'textuur' (bijv. de geur van karton, het gewicht van een plank, het gebrek aan licht).
2. Geen verkoop-praat. Geen handleidingen.
3. Focus 100% op de realiteit van de productcategorie op {{url}}.
"""

WRITER_PROMPT = f"""Jij bent een Ghostwriter voor een kritische columnist. Je haat 'content' en schrijft alleen verhalen.

JOUW STEM:
- Gebruik 'Show, Don't Tell'. Beschrijf inbussleutels, scharnieren, stofnesten en spaanplaat.
- ZINSBOUW: Varieer. Korte, botte zinnen afgewisseld met diepe observaties.
- VERBODEN: {", ".join(BLACK_LIST)}
- GEEN META: Praat nooit over de tekst zelf of 'het belang van'.

TARGET: {{section_target}} woorden.
"""

ASSEMBLER_PROMPT = """Jij bent de Eindredacteur. Smeed de teksten aaneen tot een vloeiend essay.
1. Verwijder elke zin die klinkt als marketing of AI-opvulling.
2. Verwijder conclusies zoals "Kortom" of "Samenvattend".
3. Behoud de rauwe textuur en de feiten.
"""

SCORER_PROMPT = """Jij bent een AI-detector. SCORE < 10 ALS:
- De tekst woorden uit de blacklist bevat.
- De tekst leest als een handleiding of brochure.
- De tekst te beleefd of te 'vriendelijk' is.

JSON OUTPUT:
{{
    "score": 100,
    "reasoning": "Leg uit waarom de tekst nog te veel naar AI ruikt.",
    "slop_detected": []
}}
"""

# --- AI ENGINE FUNCTIE ---
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
st.title("🛡️ Authority Engine v21.0")
st.subheader("The Final Sentinel | Industrial Grade Human-Like Content")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("Target URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Publisher", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 1500, 950, step=50)
    
    start_btn = st.button("EXECUTE PRODUCTION", type="primary")

if start_btn:
    start_time = time.time()
    with st.status("🚀 Pijplijn gestart...", expanded=True) as status:
        
        # FASE 1: ARCHITECT
        st.write("📐 Architectuur ontwerpen (Context-Lock op URL)...")
        blueprint = call_ai(f"Project: {target_url}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, url=target_url, client=client_name))
        
        # FASE 2: SEQUENTIAL WRITING
        sections = re.split(r'##', blueprint)[1:]
        full_raw_content = ""
        section_target = int(word_count_target // 4)
        
        for i, s in enumerate(sections):
            st.write(f"🖋️ Ghostwriting sectie {i+1}...")
            section_text = call_ai(f"H2 Sectie Plan: {s}", 
                                    WRITER_PROMPT.format(section_target=section_target, client=client_name))
            full_raw_content += f"\n\n## {section_text}"
            time.sleep(0.5)

        # FASE 3: ASSEMBLY & PRUNING
        st.write("✨ Assembleren en opschonen...")
        assembled_text = call_ai(f"Smeed dit aaneen tot een essay:\n{full_raw_content}", ASSEMBLER_PROMPT, temp=0.5)
        
        # FASE 4: PYTHON TECHNICAL ENFORCEMENT (De 'Iron Link')
        # We vertrouwen de AI niet. We injecteren de link zelf op de eerste match.
        try:
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            final_article = pattern.sub(f"[{anchor_text}]({target_url})", assembled_text, count=1)
        except:
            final_article = assembled_text # Fallback

        # FASE 5: AUDIT
        st.write("🧐 Finale kwaliteits-audit...")
        score_raw = call_ai(f"Audit tekst:\n\n{final_article}", SCORER_PROMPT.format(target=word_count_target), temp=0.1)
        try:
            score_data = json.loads(re.search(r'\{.*\}', score_raw, re.DOTALL).group())
            final_score = score_data.get("score", 0)
        except:
            final_score = 50
            score_data = {"reasoning": "Audit parsing failed"}

        duration = int(time.time() - start_time)
        status.update(label=f"✅ Asset Voltooid in {duration}s", state="complete")

    # --- OUTPUT ---
    tab1, tab2 = st.tabs(["💎 Final Asset", "📊 Audit Log"])
    
    with tab1:
        c_final = count_words(final_article)
        st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
        
        if final_score < 80:
            st.warning(f"Kwaliteitsscore: {final_score}/100. Reden: {score_data.get('reasoning')}")
        
        st.markdown("---")
        st.markdown(final_article)
        st.download_button("Download Markdown", final_article, file_name=f"{client_name}_asset.md")
        
    with tab2:
        st.json(score_data)
        st.text_area("Blueprint", blueprint)
