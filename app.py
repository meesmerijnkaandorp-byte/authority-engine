import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v12.0 | The Iron Link", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Kritieke fout: API-sleutel ontbreekt in Secrets.")

def count_words(text):
    return len(text.split())

# --- AGENT 1: THE ARCHITECT (Strategische Blueprint) ---
ARCHITECT_PROMPT = """Jij bent de Strategisch Directeur. Ontwerp een Paragraph Map voor {target} woorden.
URL: {url} | KLANT: {client} | PLATFORM: {platform}

EISEN:
1. FOCUS: Het artikel gaat over de productgroep op {url}. NIET over de geschiedenis van {client}.
2. STRUCTUUR: Exact 4 H2-secties.
3. NUCHTERHEID: Geen marketing-gezwets. Schrijf over de fysieke realiteit (materiaal, gebruik, ruimte).
4. LINK-PLAN: Bepaal dat de hyperlink in de eerste sectie komt.
"""

# --- AGENT 2: THE TITAN WRITER (De Harde Journalist) ---
WRITER_PROMPT = """Jij bent een nuchtere journalist. Je haat AI-slop en marketing-taal.

JOUW STIJL:
- ZWARTE LIJST (NOOIT GEBRUIKEN): oase, harmonieus, samenspel, ontdekkingsreis, beleving, esthetiek, minimalistisch, glamour, balans, duurzaamheid, baken, feniks, horizon, prachtig, ontdek.
- METHODE: Directe, korte zinnen. Geen 'verkoop-praat'. 

{link_instruction}

DOEL: Minimaal {section_target} woorden.
{feedback_instruction}
"""

# --- AGENT 3: THE ASSEMBLER (De Technisch Redacteur) ---
ASSEMBLER_PROMPT = """Jij bent de Technisch Eindredacteur. Smeed de hoofdstukken aaneen tot een essay van {target} woorden.

JOUW TECHNISCHE TAKEN:
1. HYPERLINK VALIDATIE: Er MOET exact één klikbare link in de tekst staan: [{anchor}]({url}). Als deze mist, voeg hem dan alsnog toe in de eerste alinea.
2. SLOP-VERWIJDERING: Schrap elke zin die klinkt als een samenvatting of marketing-vulling.
3. GEEN META: Verwijder elke verwijzing naar 'dit artikel' of 'deze tekst'.
4. SEO: Voeg Metadata (Title, Meta Description, Slug) toe aan de top.
"""

# --- AGENT 4: THE GATEKEEPER (De Beul) ---
SCORER_PROMPT = """Jij bent de Poortwachter. Beoordeel op target {target}.
EISEN VOOR SCORE 85+:
- De link [{anchor}]({url}) staat er EXACT één keer in.
- Geen verboden woorden (oase, baken, etc.).
- Geen fluff, geen 'AI-vibe'.

OUTPUT IN JSON:
{{
    "score": 0,
    "reasoning": "Wees brutaal.",
    "link_present": true/false,
    "improvements": "Wat moet er concreet gebeuren?"
}}
"""

# --- AI ENGINE ---
def call_ai(prompt, system_instruction, temp=0.75, response_format=None):
    try:
        args = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": temp
        }
        if response_format:
            args["response_format"] = response_format
        response = client.chat.completions.create(**args)
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v12.0")
st.subheader("The Iron Link: Kwaliteit & Hyperlink Enforced")

with st.sidebar:
    st.header("📋 Briefing")
    client_name = st.text_input("Klant", value="VidaXL NL")
    target_url = st.text_input("Target URL", value="https://www.vidaxl.nl/g/4063/kledingkasten")
    anchor_text = st.text_input("Ankertekst", value="kledingkast")
    target_domain = st.text_input("Platform", value="dagelijksestandaard.nl")
    word_count_target = st.slider("Target Woorden", 600, 1500, 900, step=50)
    
    start_btn = st.button("EXECUTE PRODUCTION", type="primary")

if start_btn:
    with st.status("🏗️ Productielijn draait (Recursive Logic)...", expanded=True) as status:
        # FASE 1: ARCHITECT
        st.write("📐 Architectuur ontwerpen...")
        blueprint = call_ai(f"Insteek voor {target_url}", 
                            ARCHITECT_PROMPT.format(target=word_count_target, client=client_name, platform=target_domain, url=target_url))
        
        final_article = ""
        score_data = {"score": 0, "link_present": False}
        attempts = 0
        max_attempts = 3

        while (score_data["score"] < 85 or not score_data["link_present"]) and attempts < max_attempts:
            attempts += 1
            st.write(f"🔄 **Poging {attempts}** van {max_attempts}...")
            
            # FASE 2: WRITING
            h2_sections = re.split(r'##', blueprint)[1:]
            full_raw_content = ""
            section_target = int((word_count_target * 1.1) // 4)
            
            feedback_instr = ""
            if attempts > 1:
                feedback_instr = f"FOUT IN VORIGE POGING: {score_data.get('reasoning')}. Herstel de hyperlink en verwijder alle AI-clichés!"

            for i, s in enumerate(h2_sections):
                # Link alleen in de eerste sectie dwingen
                if i == 0:
                    l_inst = f"TECHNISCH BEVEL: Je MOET de hyperlink exact zo schrijven: [{anchor_text}]({target_url}). Geen variaties."
                else:
                    l_inst = "GEBRUIK GEEN HYPERLINKS."
                
                st.write(f"  🖋️ Schrijven sectie {i+1}...")
                section_text = call_ai(
                    f"Sectie Instructie: {s}",
                    WRITER_PROMPT.format(section_target=section_target, client=client_name, link_instruction=l_inst, feedback_instruction=feedback_instr),
                    temp=0.8
                )
                full_raw_content += f"\n\n## {section_text}"

            # FASE 3: ASSEMBLY
            st.write("  ✨ Assembleren en technische link-check...")
            final_article = call_ai(f"Smeed aaneen tot {word_count_target} woorden. Gebruik [{anchor_text}]({target_url}) EXACT één keer:\n{full_raw_content}", 
                                    ASSEMBLER_PROMPT.format(target=word_count_target, url=target_url, anchor=anchor_text), temp=0.5)
            
            # FASE 4: SCORE (Nu met harde link-check)
            st.write("  🧐 Kwaliteitscontrole...")
            score_raw = call_ai(
                f"Beoordeel deze tekst:\n\n{final_article}", 
                SCORER_PROMPT.format(target=word_count_target, anchor=anchor_text, url=target_url), 
                temp=0.1, 
                response_format={"type": "json_object"}
            )
            score_data = json.loads(score_raw)
            
            # Extra Python validatie voor de zekerheid
            if f"[{anchor_text}]({target_url})" in final_article:
                score_data["link_present"] = True
            
            if score_data["score"] >= 85 and score_data["link_present"]:
                status.update(label=f"✅ Kwaliteit behaald (Score: {score_data['score']})", state="complete")
                break
            else:
                st.warning(f"Poging {attempts} afgekeurd. Score: {score_data['score']} | Link aanwezig: {score_data['link_present']}")

        if attempts == max_attempts and (score_data["score"] < 85 or not score_data["link_present"]):
            status.update(label=f"⚠️ Max pogingen bereikt. Check output.", state="error")

    # --- OUTPUT ---
    tab1, tab2 = st.tabs(["💎 Final Asset", "📊 Audit Log"])
    with tab1:
        c_final = count_words(final_article)
        st.metric("Volume", f"{c_final} woorden", delta=int(c_final - word_count_target))
        st.markdown(final_article)
        st.download_button("Download Markdown", final_article, file_name=f"artikel_{client_name}.md")
    with tab2:
        st.write(f"Aantal pogingen: {attempts}")
        st.json(score_data)
        st.subheader("Rauwe Tekst ter analyse:")
        st.text_area("Rauw", final_article, height=300)
