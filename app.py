import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v45.0 | The Expert Blueprint", layout="wide")

try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("Kritieke fout: API-sleutel ontbreekt in Secrets.")

CONFIG = {
    "OPENAI_MODEL": "gpt-4o",
    "ENABLE_RETRY_ON_QA_FAIL": True,
    "MIN_WORDS": 600,
    "MAX_WORDS": 1800
}

LANG_INSTRUCTIONS = {
    "NL": "Schrijf uitsluitend in foutloos, idiomatisch Nederlands op moedertaalniveau.",
    "EN": "Write exclusively in professional, native-level English.",
    "DE": "Schreiben Sie ausschließlich in fehlerfreiem, muttersprachlichem Deutsch.",
    "FR": "Écrivez exclusivement en français idiomatique et sans fautes."
}

UNIVERSAL_BAN = ["oase", "essentieel", "cruciaal", "wereld van verschil", "esthetiek", "harmonie", "samenspel", "paradigma", "fundamenteel", "belangrijkste rol", "stel je voor", "in de moderne wereld", "niet alleen ... maar ook"]

TOV_PROFILES = {
    "Expert/Adviserend (Nieuw)": {
        "instructie": "Schrijf als een doorgewinterde expert. Geef direct, concreet en praktisch advies. Noem afmetingen, specifieke materialen en harde feiten. Vermijd wollige inleidingen en filosofische bespiegelingen over sfeer.",
        "ban": UNIVERSAL_BAN + ["gezelligheid", "sfeervol", "beleving", "droom", "magisch"]
    },
    "Verhalend/Lifestyle": {
        "instructie": "Schrijf nuchter, beschouwend en verhalend, maar BLIJF CONCREET. Geen lange 'Stel je voor'-scenario's. Geef direct praktische voorbeelden.",
        "ban": UNIVERSAL_BAN + ["synergie", "optimaliseren", "implementeren"]
    },
    "Zakelijk/Technisch": {
        "instructie": "Schrijf analytisch en objectief. Focus op harde specificaties, kosten en ROI.",
        "ban": UNIVERSAL_BAN + ["gevoel", "beleving", "passie"]
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
    intent_tone = "expert advies, overtuigend en praktisch."
    target = base_target
    if re.search(r'\b(prijs|kosten|offerte|bestellen|kopen|aanbieding|deal|offer|buy|kaufen|acheter)\b', text):
        intent_tone = "commercieel adviserend, gericht op de juiste aankoopcriteria."
        target = max(base_target, 1000)
    elif re.search(r'\b(vergelijk|verschil|advies|uitleg|informatie|wat is|hoe werkt|compare|how|comment)\b', text):
        intent_tone = "informationeel expert, gericht op educatie en feiten."
        target = max(base_target, 1300)
    return intent_tone, target

def validate_output(text, ban_list):
    return {
        "ban_words_found": [w for w in ban_list if w.lower() in text.lower()],
        "no_bullets": not re.search(r'(?m)^[-*]\s', text)
    }

# --- SYSTEM PROMPTS (v45.0) ---

STRATEGIST_SYSTEM = """Jij bent een Hoofdredacteur. Je levert UITSLUITEND JSON.
TAAL: {language_instruction}
TAAK: Ontwerp een expert-artikel voor {publisher_info} gericht op {anchor}.

EXPERT-REGELS (ANTI-FLUFF):
1. Verzin 4 specifieke, actiegerichte koppen (bijv. "Waarom zithoogte de doorslag geeft" i.p.v. "Comfort en Ergonomie").
2. Geef per sectie 3 HARDE, CONCRETE adviezen of data-punten in 'key_points' (bijv. "Zithoogte 45-48cm", "60cm ruimte per stoel", "Kunststof vs Stof met kinderen").
3. Voorkom herhaling. Elke sectie is een silo met een eigen, uniek onderwerp.
4. KOPPEN: Gebruik 'Sentence case' (Alleen eerste letter is hoofdletter).

SCHEMA:
{{
  "title": "Actiegerichte kop (in sentence case)",
  "sections": [ {{ "h2": "Kop in sentence case", "key_points": ["Concreet feit 1", "Concreet feit 2", "Vuistregel 3"] }} ]
}}"""

WRITER_SYSTEM = """Jij bent een Expert/Vakjournalist.
TAAL: {language_instruction}
STIJL: {tov_instruction} Focus: {intent_tone}

ANTI-FLUFF REGELS:
1. GEEN "Stel je voor"-inleidingen. Kom direct ter zake.
2. GEEN herhalende conclusies aan het eind van de alinea (zoals "Kortom, stijl en comfort moeten in balans zijn"). Behandel puur de theorie en feiten.
3. Gebruik de specifieke `key_points` uit de briefing als harde feiten in je tekst (bijv. verwerk de centimeters of materiaal-verschillen in de zinnen).
4. GEEN BULLETPOINTS. Schrijf in lopende tekst.
5. VERBODEN WOORDEN: {ban_list}"""

EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. Je levert UITSLUITEND JSON.
TAAL: {language_instruction}
TAAK: Smeed aaneen tot ca. {target} woorden.

LINK-STRATEGIE ({mode}):
Ankertekst: '{anchor}'
Plaats de marker [ANCHOR_SPOT] exact 1x.
- Bij 'Exact Match': De tekst MOET letterlijk '{anchor}' bevatten. Als het anker grammaticaal onhandig is (bijv. infinitief zonder lidwoord), gebruik dan een vluchtstrook-zin zoals: "Wanneer het gaat om {anchor}, is het belangrijk dat..." of "Bij {anchor} letten veel mensen op...". Maak het FOUTLOOS Nederlands.
- Bij 'Natuurlijk': Verbuig de term vrijuit voor een vloeiende zin (bijv. "nieuwe eetkamerstoelen kopen").

KWALITEITSCONTROLE:
- Schrijf een KRACHTIGE, SAMENVATTENDE CONCLUSIE als laatste alinea van de `body` waarin je de belangrijkste aankoopcriteria opsomt in lopende tekst.
- Vul het veld `anchor_sentence_check` in ter controle.

SCHEMA:
{{
  "title": "Kop in sentence case", 
  "meta": "Meta", 
  "slug": "url-slug", 
  "anchor_sentence_check": "De zin met de ankertekst.",
  "body": "## Tussenkop\\n\\nTekst..."
}}"""

RETRY_EDITOR_SYSTEM = """Jij bent de Hoofdredacteur. JE VORIGE WERK WERD AFGEKEURD.
HERSTEL: 
1. VERWIJDER ELKE BULLETPOINT/OPSOMMING. Maak er lopende alinea's van.
2. KOPPEN in Sentence case.
3. Foutloze [ANCHOR_SPOT] integratie.
Lever UITSLUITEND JSON (title, meta, slug, anchor_sentence_check, body)."""

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
st.title("🛡️ Authority Engine v45.0")
st.caption("The Expert Blueprint | Concrete Feiten, Geen Fluff")

with st.sidebar:
    st.header("📋 Setup & Locatie")
    language_sel = st.selectbox("Taal", ["NL", "EN", "DE", "FR"])
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    
    st.info("💡 Tip: Bij werkwoorden (zoals 'kopen') geeft 'Natuurlijk' het beste taalkundige resultaat.")
    anchor_mode = st.radio("Link Modus", ["Exact Match", "Natuurlijk/Vloeiend"])
    
    st.divider()
    st.header("🎭 Publisher & Toon")
    tov_selection = st.selectbox("Tone of Voice", list(TOV_PROFILES.keys()), index=0)
    publisher_info = st.text_area("Publisher Niche", value="Lifestyle blog met focus op praktisch interieuradvies.")
    base_word_count = st.slider("Basis Target Woorden", CONFIG["MIN_WORDS"], CONFIG["MAX_WORDS"], 950, step=50)
    
    start_btn = st.button("PRODUCEER EXPERT ASSET", type="primary", use_container_width=True)

if start_btn:
    start_time = time.time()
    current_tov = TOV_PROFILES[tov_selection]
    ban_list_str = ", ".join(current_tov["ban"])
    lang_inst = LANG_INSTRUCTIONS[language_sel]
    
    intent_tone, dynamic_target = get_intent_and_target(anchor_text, language_sel, base_word_count)

    with st.status(f"🏗️ Expert Engine start ({language_sel})...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Fase 1: Expert Blueprint met harde feiten genereren...")
        strat_sys = STRATEGIST_SYSTEM.format(
            language_instruction=lang_inst, intent_tone=intent_tone, 
            tov_instruction=current_tov["instructie"], publisher_info=publisher_info, anchor=anchor_text
        )
        blueprint = json.loads(clean_json_string(call_ai(strat_sys, f"Target: {dynamic_target}w", json_mode=True)))

        # 2. WRITER
        st.write("🖋️ Fase 2: Schrijven met absolute Anti-Fluff dwang...")
        full_draft = ""
        sec_target = dynamic_target // len(blueprint.get("sections", [1,2,3,4]))
        
        for section in blueprint.get("sections", []):
            write_sys = WRITER_SYSTEM.format(language_instruction=lang_inst, tov_instruction=current_tov["instructie"], intent_tone=intent_tone, ban_list=ban_list_str)
            write_prompt = f"Kop: {section.get('h2')}\nData Punten / Feiten: {', '.join(section.get('key_points', []))}\nTarget: {sec_target}w."
            draft = call_ai(write_sys, write_prompt)
            full_draft += f"\n\n## {section.get('h2')}\n{draft}"

        # 3. EDITOR
        st.write("✨ Fase 3: Eindredactie & Link Kwaliteitscontrole...")
        editor_sys = EDITOR_SYSTEM.format(
            language_instruction=lang_inst, target=dynamic_target, anchor=anchor_text, 
            mode=anchor_mode, tov_instruction=current_tov["instructie"]
        )
        raw_editor = call_ai(editor_sys, f"Smeed aaneen, schrijf de eindconclusie en let op koppen:\n{full_draft}", json_mode=True)
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

    st.info(f"🔍 **AI Grammatica Check:** {final_json.get('anchor_sentence_check', 'Niet gevonden')}")

    st.markdown("---")
    st.markdown(final_json['body'])
    st.download_button("Download Markdown (.md)", final_json['body'], file_name=f"asset_expert_{language_sel}.md", use_container_width=True)
