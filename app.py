import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v43.0 | The Quality Lock", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt in Secrets.")

# --- CENTRALE ENTERPRISE CONFIGURATIE ---
CONFIG = {
    "OPENAI_MODEL": "gpt-4o",
    "ENABLE_RETRY_ON_QA_FAIL": True,
    "MIN_WORDS": 600,
    "MAX_WORDS": 1800
}

# --- TAAL INSTRUCTIES ---
LANG_INSTRUCTIONS = {
    "NL": "Schrijf uitsluitend in foutloos, idiomatisch Nederlands.",
    "EN": "Write exclusively in professional, native-level English.",
    "DE": "Schreiben Sie ausschließlich in fehlerfreiem, muttersprachlichem Deutsch.",
    "FR": "Écrivez exclusivement en français idiomatique et sans fautes."
}

# --- TONE OF VOICE DEFINITIES & EMBARGO'S ---
UNIVERSAL_BAN = ["oase", "essentieel", "cruciaal", "wereld van verschil", "esthetiek", "harmonie", "samenspel", "paradigma", "fundamenteel", "belangrijkste rol"]

TOV_PROFILES = {
    "Verhalend/Lifestyle": {
        "instructie": "Schrijf nuchter, beschouwend en verhalend. Focus op menselijke ervaring en concrete details.",
        "ban": UNIVERSAL_BAN + ["synergie", "optimaliseren", "implementeren"]
    },
    "Zakelijk/Technisch": {
        "instructie": "Schrijf professioneel, analytisch en objectief. Focus op harde specificaties en praktische bruikbaarheid.",
        "ban": UNIVERSAL_BAN + ["gevoel", "beleving", "magisch", "passie", "droom"]
    },
    "Direct/Nieuwsachtig": {
        "instructie": "Schrijf kort, to-the-point, feitelijk en urgent. Wars van marketingtaal.",
        "ban": UNIVERSAL_BAN + ["uniek", "ontdek", "adembenemend", "sfeervol"]
    }
}

# --- ROBUUSTE HELPERS ---
def count_words(text):
    return len(text.split())

def clean_json_string(raw_string):
    try:
        start = raw_string.find('{')
        end = raw_string.rfind('}') + 1
        if start != -1 and end != 0:
            return raw_string[start:end]
        return None
    except: return None

def cleanup_text(text):
    t = str(text or '')
    t = re.sub(r'\bDit Artikel\b', 'Dit artikel', t)
    t = re.sub(r'\bDeze Pagina\b', 'Deze pagina', t)
    t = re.sub(r'\bDe Specialist\b', 'de specialist', t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    return t.strip()

def get_intent_and_target(anchor, language, base_target):
    text = anchor.lower()
    intent_tone = "professioneel, overtuigend en betrouwbaar."
    target = base_target
    if re.search(r'\b(prijs|kosten|offerte|bestellen|kopen|aanbieding|deal|offer|buy|kaufen|acheter)\b', text):
        intent_tone = "commercieel, conversie-gericht en overtuigend."
        target = max(base_target, 1000)
    elif re.search(r'\b(vergelijk|verschil|advies|uitleg|informatie|wat is|hoe werkt|compare|how|comment)\b', text):
        intent_tone = "informationeel, adviserend en professioneel."
        target = max(base_target, 1300)
    return intent_tone, target

def validate_output(text, ban_list):
    return {
        "ban_words_found": [w for w in ban_list if w.lower() in text.lower()],
        "no_bullets": not re.search(r'(?m)^[-*]\s', text)
    }

# --- SYSTEM PROMPTS (v43.0 - The Quality Lock) ---

STRATEGIST_SYSTEM = """Jij bent een Hoofdredacteur. Je levert UITSLUITEND JSON.
TAAL: {language_instruction}
TAAK: Ontwerp een essay-structuur die start bij de publisher ({publisher_info}) en eindigt bij het onderwerp {anchor}.
STIJL-INSTRUCTIE: {tov_instruction}

STRICTE EISEN: 
- Plan uitsluitend LOPENDE alinea's. GEEN bulletpoints.
- KOPPEN: Gebruik 'Sentence case'. Alleen het eerste woord krijgt een hoofdletter.

SCHEMA:
{{
  "title": "Pakkende kop (in sentence case)",
  "sections": [ {{ "h2": "Kop in sentence case", "focus": "Focus", "friction": "Het probleem" }} ]
}}"""

WRITER_SYSTEM = """Jij bent een Senior Vakjournalist.
TAAL: {language_instruction}
STIJL & INTENTIE: {tov_instruction} Focus op: {intent_tone}

STRICTE EISEN:
1. GEEN BULLETPOINTS, GEEN OPSOMMINGEN. Schrijf uitsluitend in vloeiende alinea's.
2. VERBODEN WOORDEN: {ban_list}
3. HOOFDLETTERS IN KOPPEN: Gebruik uitsluitend 'Sentence case' (bijv. "De impact van materiaal", NIET "De Impact Van Materiaal")."""

EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. Je levert UITSLUITEND JSON.
TAAL: {language_instruction}
TAAK: Smeed de hoofdstukken aaneen tot een naadloos geheel van ca. {target} woorden.

LINK-STRATEGIE ({mode}):
Ankertekst: '{anchor}'
Plaats exact 1x de marker [ANCHOR_SPOT] in de tekst.
- Exact Match: De zin MOET grammaticaal foutloos zijn als je exact de woorden '{anchor}' invult. Gebruik sjablonen zoals: 
  "Een [ANCHOR_SPOT] doe je niet zomaar...", 
  "Online een [ANCHOR_SPOT] wordt steeds populairder...", 
  "In de zoektocht naar de perfecte inrichting is een [ANCHOR_SPOT] vaak de laatste stap."
- Natuurlijk: Verbuig de term (bijv. meervoud, of voeg lidwoorden toe) zodat het 100% natuurlijk klinkt.

KWALITEITSCONTROLE:
Voordat je de body schrijft, vul je het veld "anchor_sentence_check" in. Schrijf hier de exacte zin op en controleer of dit écht een goedlopende Nederlandse zin is.

SCHEMA:
{{
  "title": "Definitieve kop in sentence case", 
  "meta": "Meta description", 
  "slug": "url-slug", 
  "anchor_sentence_check": "Schrijf hier de exacte zin met de ankertekst en valideer de grammatica",
  "body": "## Tussenkop in sentence case\\n\\nTekst met de kloppende [ANCHOR_SPOT] zin..."
}}"""

RETRY_EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. JE VORIGE WERK WERD AFGEKEURD DOOR DE QA.
HERSTELOPDRACHT: 
1. Herschrijf de tekst. VERWIJDER ELKE BULLETPOINT EN OPSOMMING. Maak er lopende alinea's van.
2. KOPPEN: Zorg dat koppen Sentence case hebben.
3. Behoud de [ANCHOR_SPOT] integratie in een FOUTLOZE zin.
Lever UITSLUITEND JSON volgens het schema (title, meta, slug, anchor_sentence_check, body)."""

# --- AI WRAPPER ---
def call_ai(system, prompt, temp=0.7, json_mode=False):
    response = client.chat.completions.create(
        model=CONFIG["OPENAI_MODEL"],
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=temp,
        response_format={"type": "json_object"} if json_mode else None
    )
    return response.choices[0].message.content

# --- UI INTERFACE ---
st.title("🛡️ Authority Engine v43.0")
st.caption("The Quality Lock | Geforceerde Grammatica Controle")

with st.sidebar:
    st.header("📋 Setup & Locatie")
    language_sel = st.selectbox("Taal", ["NL", "EN", "DE", "FR"])
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    anchor_mode = st.radio("Link Modus", ["Exact Match", "Natuurlijk/Vloeiend"])
    
    st.divider()
    st.header("🎭 Publisher & Toon")
    tov_selection = st.selectbox("Tone of Voice", list(TOV_PROFILES.keys()))
    publisher_info = st.text_area("Publisher Niche", value="Culinaire website met eenvoudige recepten en de biologische citroen in de hoofdrol.")
    base_word_count = st.slider("Basis Target Woorden", CONFIG["MIN_WORDS"], CONFIG["MAX_WORDS"], 950, step=50)
    
    start_btn = st.button("PRODUCEER KWALITEITS ASSET", type="primary", use_container_width=True)

if start_btn:
    start_time = time.time()
    current_tov = TOV_PROFILES[tov_selection]
    ban_list_str = ", ".join(current_tov["ban"])
    lang_inst = LANG_INSTRUCTIONS[language_sel]
    
    intent_tone, dynamic_target = get_intent_and_target(anchor_text, language_sel, base_word_count)

    with st.status(f"🏗️ Engine start ({language_sel})...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Fase 1: Structuur bouwen...")
        strat_sys = STRATEGIST_SYSTEM.format(
            language_instruction=lang_inst, intent_tone=intent_tone, 
            tov_instruction=current_tov["instructie"], publisher_info=publisher_info, anchor=anchor_text
        )
        blueprint = json.loads(clean_json_string(call_ai(strat_sys, f"Target: {dynamic_target}w", json_mode=True)))

        # 2. WRITER
        st.write("🖋️ Fase 2: Schrijven met Native Dwang...")
        full_draft = ""
        sec_target = dynamic_target // len(blueprint.get("sections", [1,2,3,4]))
        
        for section in blueprint.get("sections", []):
            write_sys = WRITER_SYSTEM.format(language_instruction=lang_inst, tov_instruction=current_tov["instructie"], intent_tone=intent_tone, ban_list=ban_list_str)
            write_prompt = f"Kop: {section.get('h2')}\nFocus: {section.get('focus')}\nFrictie: {section.get('friction')}\nTarget: {sec_target}w."
            draft = call_ai(write_sys, write_prompt)
            full_draft += f"\n\n## {section.get('h2')}\n{draft}"

        # 3. EDITOR
        st.write("✨ Fase 3: Eindredactie & Link Kwaliteitscontrole...")
        editor_sys = EDITOR_SYSTEM.format(
            language_instruction=lang_inst, target=dynamic_target, anchor=anchor_text, 
            mode=anchor_mode, tov_instruction=current_tov["instructie"]
        )
        raw_editor = call_ai(editor_sys, f"Smeed aaneen, let op je hoofdletters in koppen:\n{full_draft}", json_mode=True)
        final_json = json.loads(clean_json_string(raw_editor))

        # --- QA & RETRY ---
        qa_result = validate_output(final_json.get("body", ""), current_tov["ban"])
        if (not qa_result["no_bullets"] or qa_result["ban_words_found"]) and CONFIG["ENABLE_RETRY_ON_QA_FAIL"]:
            st.warning("⚠️ QA Faalde. Retry Editor wordt gestart...")
            retry_sys = RETRY_EDITOR_SYSTEM.format(lang_code=language_sel)
            raw_retry = call_ai(retry_sys, f"Oorspronkelijke output:\n{final_json.get('body')}", temp=0.4, json_mode=True)
            final_json = json.loads(clean_json_string(raw_retry))
            st.success("✅ Retry succesvol afgerond.")

        # 4. PYTHON LINK INJECTION
        body = final_json.get("body", "")
        if "[ANCHOR_SPOT]" in body:
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        else:
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            body = pattern.sub(f"[{anchor_text}]({target_url})", body, count=1)
        
        final_json["body"] = cleanup_text(body)
        status.update(label=f"✅ Content Ready in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    qa_final = validate_output(final_json['body'], current_tov["ban"])
    
    st.header(final_json.get('title'))
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Volume", f"{count_words(final_json['body'])} w")
    col2.metric("Link", "✅ Aanwezig" if f"({target_url})" in final_json['body'] else "❌ Ontbreekt")
    col3.metric("Bullet-Vrij", "✅ Ja" if qa_final['no_bullets'] else "❌ Nee")
    col4.metric("Ban-List", "✅ Schoon" if not qa_final['ban_words_found'] else f"❌ Fout")

    # DE NIEUWE KWALITEITSCHECK ZICHTBAAR MAKEN
    st.info(f"🔍 **AI Grammatica Check:** {final_json.get('anchor_sentence_check', 'Niet gevonden')}")

    st.markdown("---")
    st.markdown(final_json['body'])
    st.download_button("Download Markdown (.md)", final_json['body'], file_name=f"asset_{language_sel}.md", use_container_width=True)
