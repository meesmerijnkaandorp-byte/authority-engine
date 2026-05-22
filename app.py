import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v49.0 | Two-Pass Pipeline", layout="wide")

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
    "NL": "Schrijf het volledige artikel uitsluitend in professioneel, idiomatisch Nederlands op moedertaalniveau. Gebruik een vloeiende, natuurlijke en overtuigende schrijfstijl. Vermijd letterlijk vertaalde formuleringen.",
    "EN": "Write the full article exclusively in professional, idiomatic English at native level. Use a smooth, natural, expert, and persuasive writing style.",
    "DE": "Schreiben Sie das vollständige Artikel ausschließlich in professionellem, idiomatischem Deutsch auf Muttersprachniveau. Verwenden Sie einen fließenden, natürlichen und überzeugenden Schreibstil.",
    "FR": "Écrivez l'article exclusivement en français professionnel et idiomatique de niveau langue maternelle. Utilisez un style d'écriture fluide, naturel et convaincant."
}

UNIVERSAL_BAN = [
    "oase", "essentieel", "cruciaal", "wereld van verschil", "esthetiek", "esthetisch", "harmonie", "samenspel", 
    "paradigma", "fundamenteel", "belangrijkste rol", "stel je voor", "in de moderne wereld", 
    "niet alleen ... maar ook", "ultieme", "ongeëvenaard", "tegenwoordig", "meer dan ooit"
]

TOV_PROFILES = {
    "Expert/Adviserend": {
        "instructie": "Schrijf als een doorgewinterde, onafhankelijke expert. Geef direct, concreet en praktisch advies gebaseerd op harde feiten. De lezer zoekt autoriteit. Wees stellig maar genuanceerd. Noem afmetingen, materialen, en harde vuistregels. Vermijd filosofische bespiegelingen.",
        "ban": UNIVERSAL_BAN + ["gezelligheid", "sfeervol", "beleving", "droom", "magisch", "knus"]
    },
    "Verhalend/Lifestyle": {
        "instructie": "Schrijf nuchter, beschouwend en verhalend. Gebruik de 'zaterdagmorgen-energie': herkenbare details in het dagelijks leven. Vermijd abstracte marketingtaal. Maak de tekst tastbaar door zintuiglijke details te benoemen.",
        "ban": UNIVERSAL_BAN + ["synergie", "optimaliseren", "implementeren", "efficiëntie"]
    },
    "Zakelijk/Technisch": {
        "instructie": "Schrijf professioneel, analytisch, B2B-gericht en objectief. Focus op specificaties, kosten, ROI en bruikbaarheid. De tekst moet klinken als een whitepaper.",
        "ban": UNIVERSAL_BAN + ["gevoel", "beleving", "passie", "thuis", "knus"]
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
    intent_tone = "bied diepgaande educatie en betrouwbaar expert-advies."
    target = base_target
    if re.search(r'\b(prijs|kosten|offerte|bestellen|kopen|aanbieding|deal|offer|buy|kaufen|acheter)\b', text):
        intent_tone = "wees commercieel adviserend, stuur aan op de juiste aankoopbeslissing met concrete argumenten."
        target = max(base_target, 1000)
    elif re.search(r'\b(vergelijk|verschil|advies|uitleg|informatie|wat is|hoe werkt|compare|how|comment)\b', text):
        intent_tone = "wees puur informationeel, leg uit hoe dingen werken en weeg opties feitelijk af."
        target = max(base_target, 1300)
    return intent_tone, target

def validate_output(text, target_url, ban_list):
    return {
        "link_present": f"({target_url})" in text,
        "ban_words_found": [w for w in ban_list if w.lower() in text.lower()],
        "no_bullets": not re.search(r'(?m)^[-*]\s', text)
    }

def get_fallback_sentence(language, anchor_text, target_url):
    if language == "NL": return f"Meer praktische informatie en opties voor een [{anchor_text}]({target_url}) vind je online."
    if language == "EN": return f"For more practical information regarding a [{anchor_text}]({target_url}), consult a specialized provider."
    if language == "DE": return f"Weitere praktische Informationen für ein [{anchor_text}]({target_url}) finden Sie online."
    if language == "FR": return f"Pour plus d'informations pratiques concernant un [{anchor_text}]({target_url}), consultez les options en ligne."
    return f"Meer informatie: [{anchor_text}]({target_url})."

# --- ONGECOMPROMITTEERDE SYSTEM PROMPTS (v49.0) ---

STRATEGIST_SYSTEM = """Jij bent een Meesterlijke Content Architect. Je levert UITSLUITEND JSON.
TAAL: {language_instruction}
TONE OF VOICE: {tov_instruction}
INTENTIE: {intent_tone}

TAAK:
1. USE-CASE BRUG: Hoe gebruikt de lezer van {publisher_info} het product ({anchor}) fysiek? Verbind dit.
2. EXPERT DATA: Bedenk per hoofdstuk 3 snoeiharde, concrete datapunten (afmetingen, feiten, materiaalverschillen).
3. STRUCTUUR: Plan 4 of 5 unieke secties.
4. KOPPEN: Gebruik uitsluitend 'Sentence case' voor alle koppen.

SCHEMA:
{{
  "title": "Sterke kop (Sentence case)",
  "use_case_bridge": "Jouw brug tussen publisher en product.",
  "sections": [
    {{ 
      "h2": "Tussenkop in sentence case", 
      "key_points": ["Hard feit 1", "Diepgaand inzicht 2", "Vuistregel 3"],
      "friction": "Welk probleem lossen we hier op?"
    }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een Senior Vakjournalist. 
TAAL: {language_instruction}
STIJL: {tov_instruction} 

JOUW SCHRIJFWETTEN:
1. ABSOLUTE LENGTE: Schrijf zéér uitgebreid. Minimaal {sec_target} woorden. Werk de datapunten diepgaand uit.
2. GEEN OPSOMMINGEN: Schrijf uitsluitend in lange, lopende alinea's. GEEN bulletpoints.
3. ANTI-FLUFF: GEEN inleidingen zoals "Stel je voor...". Geef de lezer direct waarde en feiten.
4. VERBODEN WOORDEN: Gebruik NOOIT deze woorden: {ban_list}.

Schrijf uitsluitend de tekst voor dit specifieke hoofdstuk."""

WEAVER_SYSTEM = """Jij bent de Meedogenloze Eindredacteur. Je ontvangt een ruw, lang artikel. 
JOUW OUTPUT IS UITSLUITEND PLATTE MARKDOWN TEKST. GEEN JSON!

TAAL: {language_instruction}
STIJL: {tov_instruction}

JOUW TAKEN:
1. INKORT-VERBOD: Behoud de volledige lengte en diepgang van de originele tekst.
2. BAN-WORDS ZUIVEREN: Inspecteer de tekst. Als je woorden ziet als 'essentieel', 'cruciaal', 'esthetisch' of 'esthetiek', herschrijf je die zin direct! VERBODEN WOORDEN: {ban_list}.
3. BULLET-ZUIVERING: Als er opsommingen of streepjes (-) in staan, maak je er lopende alinea's van.
4. DE ANKERTEKST: Plaats EXACT ÉÉN KEER in de tekst de marker [ANCHOR_SPOT] voor de term '{anchor}'. 
   - Modus ({mode}): Verwerk deze term op de meest vloeiende, onzichtbare manier in een bestaande alinea. Geen geforceerde introducties. De zin moet 100% kloppend Nederlands zijn.
5. CONCLUSIE: Schrijf helemaal aan het einde één krachtige, afsluitende alinea.

Lever uitsluitend de gezuiverde Markdown tekst af. Zorg dat koppen (##) behouden blijven."""

PACKAGER_SYSTEM = """Jij bent de Data Verpakker. Je ontvangt een perfect geoptimaliseerd artikel.
Jouw enige taak is dit artikel te lezen en het netjes in JSON-formaat te verpakken.
Pas de inhoud van de tekst NIET aan. 

SCHEMA:
{{
  "title": "Een pakkende titel gebaseerd op de tekst (Sentence case)",
  "meta": "SEO meta description van max 155 tekens",
  "slug": "url-slug",
  "body": "[Hier plak je de VOLLEDIGE, EXACTE tekst die je in de prompt hebt ontvangen, inclusief alle ## koppen en de [ANCHOR_SPOT]]"
}}"""

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
st.title("🛡️ Authority Engine v49.0")
st.caption("The Two-Pass Pipeline | Absolute focus op linguïstische kwaliteit")

with st.sidebar:
    st.header("📋 Setup & Locatie")
    language_sel = st.selectbox("Taal", ["NL", "EN", "DE", "FR"])
    target_url = st.text_input("URL", value="https://www.vidaxl.nl/g/6064/eetkamerstoelen")
    anchor_text = st.text_input("Ankertekst", value="eetkamerstoel kopen")
    anchor_mode = st.radio("Link Modus", ["Exact Match", "Natuurlijk/Vloeiend"])
    
    st.divider()
    st.header("🎭 Publisher & Toon")
    tov_selection = st.selectbox("Tone of Voice", list(TOV_PROFILES.keys()), index=0)
    publisher_info = st.text_area("Publisher Niche", value="Culinaire website met eenvoudige recepten en de biologische citroen in de hoofdrol.")
    base_word_count = st.slider("Basis Target Woorden", CONFIG["MIN_WORDS"], CONFIG["MAX_WORDS"], 950, step=50)
    
    start_btn = st.button("PRODUCEER PREMIUM ASSET", type="primary", use_container_width=True)

if start_btn:
    start_time = time.time()
    current_tov = TOV_PROFILES[tov_selection]
    ban_list_str = ", ".join(current_tov["ban"])
    lang_inst = LANG_INSTRUCTIONS[language_sel]
    
    intent_tone, dynamic_target = get_intent_and_target(anchor_text, language_sel, base_word_count)

    with st.status(f"🏗️ Engine start ({language_sel}) - Target: {dynamic_target}w...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Fase 1: Blueprint genereren...")
        strat_sys = STRATEGIST_SYSTEM.format(
            language_instruction=lang_inst, tov_instruction=current_tov["instructie"],
            intent_tone=intent_tone, publisher_info=publisher_info, anchor=anchor_text
        )
        
        raw_strat = call_ai(strat_sys, f"Target: {dynamic_target}w", json_mode=True)
        blueprint = json.loads(clean_json_string(raw_strat) or "{}")
        
        # 2. WRITER (Parallel Section Generation)
        st.write("🖋️ Fase 2: Concepttekst schrijven (in silo's)...")
        full_draft = ""
        sec_target = dynamic_target // max(1, len(blueprint.get("sections", [1,2,3,4])))
        
        for section in blueprint.get("sections", []):
            write_sys = WRITER_SYSTEM.format(
                language_instruction=lang_inst, tov_instruction=current_tov["instructie"], 
                intent_tone=intent_tone, ban_list=ban_list_str, sec_target=sec_target
            )
            write_prompt = f"Kop: {section.get('h2')}\nFeiten om te verwerken: {', '.join(section.get('key_points', []))}"
            draft = call_ai(write_sys, write_prompt)
            full_draft += f"## {section.get('h2')}\n{draft}\n\n"

        # 3. THE WEAVER (The Magic Step - Plain text parsing!)
        st.write("✨ Fase 3: The Weaver (Kwaliteit en Ban-words opschonen)...")
        weaver_sys = WEAVER_SYSTEM.format(
            language_instruction=lang_inst, tov_instruction=current_tov["instructie"],
            ban_list=ban_list_str, anchor=anchor_text, mode=anchor_mode
        )
        weaved_text = call_ai(weaver_sys, f"Zuiver dit artikel. Maak het vloeiend, lang, en integreer de [ANCHOR_SPOT]:\n\n{full_draft}", json_mode=False)

        # 4. THE PACKAGER (Safe JSON packaging)
        st.write("📦 Fase 4: The Packager (JSON verpakken)...")
        packager_raw = call_ai(PACKAGER_SYSTEM, f"Lees deze tekst en verpak het EXACT in JSON:\n\n{weaved_text}", json_mode=True)
        
        try:
            final_json = json.loads(clean_json_string(packager_raw))
            assembled_body = final_json.get("body", weaved_text) # Fallback to raw text if parsing fails
        except:
            st.error("Packager faalde, fallback naar platte tekst.")
            final_json = {"title": "Gegenereerd Artikel"}
            assembled_body = weaved_text

        # 5. PYTHON LINK INJECTION & IRON FALLBACK
        if "[ANCHOR_SPOT]" in assembled_body:
            assembled_body = assembled_body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            assembled_body = assembled_body.replace("[ANCHOR_SPOT]", anchor_text)
        elif re.search(re.escape(anchor_text), assembled_body, re.IGNORECASE):
            assembled_body = re.sub(re.escape(anchor_text), f"[{anchor_text}]({target_url})", assembled_body, count=1, flags=re.IGNORECASE)
        else:
            fallback_str = get_fallback_sentence(language_sel, anchor_text, target_url)
            assembled_body += f"\n\n{fallback_str}"
            st.info("💡 Systeem ingreep: AI negeerde de ankertekst. Geforceerde linguïstische fallback toegepast.")

        final_json["body"] = cleanup_text(assembled_body)
        qa_final = validate_output(final_json['body'], target_url, current_tov["ban"])
        
        status.update(label=f"✅ Content Ready in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    st.header(final_json.get('title', 'Nieuw Artikel'))
    
    col1, col2, col3, col4 = st.columns(4)
    final_wc = count_words(final_json['body'])
    col1.metric("Volume", f"{final_wc} w", delta=final_wc - dynamic_target)
    col2.metric("Link", "✅ Aanwezig" if qa_final["link_present"] else "❌ FOUT")
    col3.metric("Bullet-Vrij", "✅ Ja" if qa_final['no_bullets'] else "❌ Nee")
    col4.metric("Ban-List", "✅ Schoon" if not qa_final['ban_words_found'] else f"❌ Fout ({len(qa_final['ban_words_found'])})")

    st.markdown("---")
    st.markdown(final_json['body'])
    st.download_button("Download Markdown (.md)", final_json['body'], file_name=f"asset_{language_sel}.md", use_container_width=True)
