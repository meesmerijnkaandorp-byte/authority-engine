import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v52.0 | The Human Touch", layout="wide")

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
    "NL": "Schrijf het volledige artikel uitsluitend in professioneel, idiomatisch Nederlands op moedertaalniveau. Gebruik een vloeiende, menselijke en overtuigende schrijfstijl. Vermijd letterlijk vertaalde formuleringen.",
    "EN": "Write the full article exclusively in professional, idiomatic English at native level. Use a smooth, natural, expert, and persuasive writing style.",
    "DE": "Schreiben Sie das vollständige Artikel ausschließlich in professionellem, idiomatischem Deutsch auf Muttersprachniveau. Verwenden Sie einen fließenden, natürlichen und überzeugenden Schreibstil.",
    "FR": "Écrivez l'article exclusivement en français professionnel et idiomatique de niveau langue maternelle. Utilisez un style d'écriture fluide, naturel et convaincant."
}

# De zwarte lijst is fors uitgebreid met de typische "AI-wrap-up" woorden.
UNIVERSAL_BAN = [
    "oase", "essentieel", "cruciaal", "wereld van verschil", "esthetiek", "esthetisch", "harmonie", "samenspel", 
    "paradigma", "fundamenteel", "belangrijkste rol", "stel je voor", "in de moderne wereld", 
    "niet alleen ... maar ook", "ultieme", "ongeëvenaard", "tegenwoordig", "meer dan ooit",
    "weloverwogen keuze", "draagt bij aan", "functionele en aantrekkelijke", "kortom", "concluderend"
]

TOV_PROFILES = {
    "Expert/Adviserend (Menselijk)": {
        "instructie": "Schrijf als een directe, ervaren expert. GEEN modelmatige AI-structuren. Geef rauw, concreet en praktisch advies. Voorbeeld van de toon: 'Een stoel kan er prachtig uitzien, maar als je na twintig minuten al verzit, heb je er weinig aan.' Vermijd elke vorm van filosofische bespiegeling.",
        "ban": UNIVERSAL_BAN + ["gezelligheid", "sfeervol", "beleving", "droom", "magisch", "knus"]
    },
    "Verhalend/Lifestyle": {
        "instructie": "Schrijf nuchter, beschouwend en menselijk. Gebruik de 'zaterdagmorgen-energie'. Maak de tekst tastbaar met concrete voorbeelden (bijv. 'Bij een gezin met jonge kinderen is een stoffen stoel minder handig dan kunstleer').",
        "ban": UNIVERSAL_BAN + ["synergie", "optimaliseren", "implementeren", "efficiëntie"]
    },
    "Zakelijk/Technisch": {
        "instructie": "Schrijf professioneel en to-the-point voor B2B. Focus op specificaties en ROI, maar blijf menselijk en direct. Geen robotachtige opsommingen.",
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

def enforce_sentence_case(text):
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        if line.strip().startswith('#'):
            match = re.match(r'^([#]+)\s+(.*)', line)
            if match:
                prefix = match.group(1)
                content = match.group(2).strip()
                new_lines.append(f"{prefix} {content.capitalize()}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

def apply_python_ban_hammer(text):
    replacements = {
        "essentieel": "onmisbaar",
        "cruciaal": "doorslaggevend",
        "cruciale": "grote",
        "wereld van verschil": "groot verschil",
        "esthetiek": "vormgeving",
        "esthetisch": "visueel",
        "harmonie": "balans",
        "samenspel": "wisselwerking",
        "weloverwogen keuze": "goede keuze",
        "draagt bij aan": "zorgt voor",
        "functionele en aantrekkelijke": "praktische"
    }
    
    for bad, good in replacements.items():
        def repl(m):
            word = m.group()
            if word.istitle(): return good.capitalize()
            elif word.isupper(): return good.upper()
            return good
        text = re.sub(rf'\b{bad}\b', repl, text, flags=re.IGNORECASE)
    return text

def cleanup_text(text):
    t = str(text or '')
    t = re.sub(r'\bDit Artikel\b', 'Dit artikel', t)
    t = re.sub(r'\bDeze Pagina\b', 'Deze pagina', t)
    t = re.sub(r'\bDe Specialist\b', 'de specialist', t)
    t = re.sub(r'[ \t]+\n', '\n', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    t = enforce_sentence_case(t)
    t = apply_python_ban_hammer(t)
    return t.strip()

def get_intent_and_target(anchor, language, base_target):
    text = anchor.lower()
    intent_tone = "bied direct toepasbaar expert-advies met harde voorbeelden."
    target = base_target
    if re.search(r'\b(prijs|kosten|offerte|bestellen|kopen|aanbieding|deal|offer|buy|kaufen|acheter)\b', text):
        intent_tone = "wees sturend en geef concrete aankoopcriteria, zonder commercieel te schreeuwen."
        target = max(base_target, 1000)
    elif re.search(r'\b(vergelijk|verschil|advies|uitleg|informatie|wat is|hoe werkt|compare|how|comment)\b', text):
        intent_tone = "wees puur informationeel, gebruik vergelijkingen uit de praktijk."
        target = max(base_target, 1300)
    return intent_tone, target

def validate_output(text, target_url, ban_list):
    return {
        "link_present": f"({target_url})" in text,
        "ban_words_found": [w for w in ban_list if w.lower() in text.lower()],
        "no_bullets": not re.search(r'(?m)^[-*]\s', text)
    }

def get_fallback_sentence(language, anchor_text, target_url):
    if language == "NL": return f"Ga je een [{anchor_text}]({target_url}), kijk dan goed naar de opties die online beschikbaar zijn."
    if language == "EN": return f"If you are looking for a [{anchor_text}]({target_url}), be sure to compare the practical options online."
    if language == "DE": return f"Wenn Sie ein [{anchor_text}]({target_url}), achten Sie auf die praktischen Optionen."
    if language == "FR": return f"Si vous cherchez un [{anchor_text}]({target_url}), comparez bien les options pratiques."
    return f"Meer informatie: [{anchor_text}]({target_url})."

# --- ONGECOMPROMITTEERDE SYSTEM PROMPTS (v52.0) ---

STRATEGIST_SYSTEM = """Jij bent een Meesterlijke Content Architect. Je levert UITSLUITEND JSON.
TAAL: {language_instruction}
TONE OF VOICE: {tov_instruction}
INTENTIE: {intent_tone}

TAAK:
1. MENSELIJKE STRUCTUUR: Maak het NIET te perfect of modelmatig. Mensen denken niet in perfect symmetrische Wikipedia-koppen. Bedenk directe, praktische invalshoeken.
2. CONCRETE DATA: Geef per sectie 3 zeer specifieke, dagelijkse voorbeelden. (bijv. "Stoffen stoel vs kinderen", "20 minuten zitten").
3. KOPPEN: Gebruik uitsluitend kleine letters voor alle woorden in de kop, behalve het allereerste woord.

SCHEMA:
{{
  "title": "Dit is een sterke kop zonder onnodige hoofdletters",
  "sections": [
    {{ 
      "h2": "Dit is een directe tussenkop", 
      "key_points": ["Concreet voorbeeld 1", "Harde eis 2", "Praktijkgeval 3"],
      "friction": "Welke herkenbare irritatie lossen we op?"
    }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een Senior Vakjournalist. 
TAAL: {language_instruction}
STIJL: {tov_instruction} 

JOUW SCHRIJFWETTEN:
1. MENSELIJK EN DIRECT: Vermijd "AI-taal" en perfecte, voorspelbare alinea's. Schrijf zoals je praat tegen een vriend. Bijvoorbeeld: "Een stoel kan er prachtig uitzien, maar als je na twintig minuten al verzit, heb je er weinig aan."
2. EXTREEM CONCREET: Gebruik altijd praktische details uit het echte leven. Bijvoorbeeld: "Bij een gezin met jonge kinderen is een stoffen stoel minder handig dan kunstleer of kunststof."
3. GEEN ALGEMENE SLOTZINNEN: Sluit je alinea NOOIT af met voorspelbare clichés zoals "Een weloverwogen keuze draagt bij aan een functionele ruimte." Geef je advies en stop met praten.
4. LENGTE ZONDER FLUFF: Haal de {sec_target} woorden door diep in voorbeelden te duiken, niet door theorie te herhalen.
5. GEEN OPSOMMINGEN: Schrijf uitsluitend in lopende alinea's.
6. VERBODEN WOORDEN: {ban_list}.

Schrijf uitsluitend de tekst voor dit specifieke hoofdstuk."""

WEAVER_SYSTEM = """Jij bent de Meedogenloze Eindredacteur. Je ontvangt een ruw artikel.
JOUW OUTPUT IS UITSLUITEND PLATTE MARKDOWN TEKST. GEEN JSON!

TAAL: {language_instruction}

JOUW TAKEN:
1. TARGET LENGTE: Smeed de tekst samen tot EXACT rond de {target} woorden (+/- 10%). Behoud de feitelijke diepgang en de concrete voorbeelden.
2. VERBODEN WOORDEN & SLOTZINNEN ZUIVEREN: Verwijder vage AI-conclusies aan het einde van alinea's (zoals "Dit draagt bij aan een optimaal resultaat"). Schrap woorden uit de {ban_list}.
3. BULLET-ZUIVERING: Verwijder eventuele opsommingen en maak er lopende zinnen van.
4. DE ANKERTEKST NATUURLIJK INVOEGEN: Plaats EXACT ÉÉN KEER de marker [ANCHOR_SPOT] voor de term '{anchor}'. 
   - Modus ({mode}): Als het anker lastig of lelijk is (zoals 'eetkamerstoel kopen'), gebruik dan deze verplichte natuurlijke constructie: 
     "Ga je een [ANCHOR_SPOT], kijk dan niet alleen naar het ontwerp, maar ook naar..." of "Besluit je online een [ANCHOR_SPOT], let dan goed op...". Maak het 100% menselijk.
5. GEEN VAGE CONCLUSIES: Voeg alleen een zeer directe, actiegerichte afsluiting toe. Geen clichés.

Lever uitsluitend de gezuiverde Markdown tekst af. Zorg dat koppen (##) behouden blijven."""

PACKAGER_SYSTEM = """Jij bent de Data Verpakker. Je ontvangt een perfect geoptimaliseerd artikel.
Jouw enige taak is dit artikel te lezen en het netjes in JSON-formaat te verpakken.
Pas de inhoud van de tekst NIET aan. 

SCHEMA:
{{
  "title": "Titel in sentence case (kleine letters behalve het eerste woord)",
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
st.title("🛡️ Authority Engine v52.0")
st.caption("The Human Touch | Rauwe zinnen, harde voorbeelden & perfecte SEO-integratie")

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
    base_word_count = st.slider("Target Woorden (Strak)", CONFIG["MIN_WORDS"], CONFIG["MAX_WORDS"], 950, step=50)
    
    start_btn = st.button("PRODUCEER PREMIUM ASSET", type="primary", use_container_width=True)

if start_btn:
    start_time = time.time()
    current_tov = TOV_PROFILES[tov_selection]
    ban_list_str = ", ".join(current_tov["ban"])
    lang_inst = LANG_INSTRUCTIONS[language_sel]
    
    intent_tone, dynamic_target = get_intent_and_target(anchor_text, language_sel, base_word_count)

    with st.status(f"🏗️ Engine start ({language_sel}) - Strak Doel: {dynamic_target}w...", expanded=True) as status:
        
        # 1. STRATEGIST
        st.write("📐 Fase 1: Asymmetrische Blueprint genereren...")
        strat_sys = STRATEGIST_SYSTEM.format(
            language_instruction=lang_inst, tov_instruction=current_tov["instructie"],
            intent_tone=intent_tone, publisher_info=publisher_info, anchor=anchor_text
        )
        
        raw_strat = call_ai(strat_sys, f"Target: {dynamic_target}w", json_mode=True)
        blueprint = json.loads(clean_json_string(raw_strat) or "{}")
        
        # 2. WRITER
        st.write("🖋️ Fase 2: Concepttekst schrijven met harde praktijkvoorbeelden...")
        full_draft = ""
        sec_target = dynamic_target // max(1, len(blueprint.get("sections", [1,2,3,4])))
        
        for section in blueprint.get("sections", []):
            write_sys = WRITER_SYSTEM.format(
                language_instruction=lang_inst, tov_instruction=current_tov["instructie"], 
                intent_tone=intent_tone, ban_list=ban_list_str, sec_target=sec_target
            )
            write_prompt = f"Kop: {section.get('h2')}\nConcrete voorbeelden om te verwerken: {', '.join(section.get('key_points', []))}"
            draft = call_ai(write_sys, write_prompt)
            full_draft += f"## {section.get('h2')}\n{draft}\n\n"

        # 3. THE WEAVER
        st.write("✨ Fase 3: The Weaver (Kwaliteit, Target lengte & Link integratie)...")
        weaver_sys = WEAVER_SYSTEM.format(
            language_instruction=lang_inst, tov_instruction=current_tov["instructie"],
            ban_list=ban_list_str, anchor=anchor_text, mode=anchor_mode, target=dynamic_target
        )
        weaved_text = call_ai(weaver_sys, f"Sloop alle AI-wrap-up zinnen eruit, smeed het tot circa {dynamic_target} woorden en integreer de [ANCHOR_SPOT] natuurlijk:\n\n{full_draft}", json_mode=False)

        # 4. THE PACKAGER
        st.write("📦 Fase 4: The Packager (JSON verpakken)...")
        packager_raw = call_ai(PACKAGER_SYSTEM, f"Lees deze tekst en verpak het EXACT in JSON:\n\n{weaved_text}", json_mode=True)
        
        try:
            final_json = json.loads(clean_json_string(packager_raw))
            assembled_body = final_json.get("body", weaved_text) 
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

        # De genadeloze Python Hammer en Cleanup
        final_json["body"] = cleanup_text(assembled_body)
        if "title" in final_json:
            final_json["title"] = final_json["title"].capitalize()

        qa_final = validate_output(final_json['body'], target_url, current_tov["ban"])
        status.update(label=f"✅ Content Ready in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    st.header(final_json.get('title', 'Nieuw artikel'))
    
    col1, col2, col3, col4 = st.columns(4)
    final_wc = count_words(final_json['body'])
    col1.metric("Volume", f"{final_wc} w", delta=final_wc - dynamic_target)
    col2.metric("Link", "✅ Aanwezig" if qa_final["link_present"] else "❌ FOUT")
    col3.metric("Bullet-Vrij", "✅ Ja" if qa_final['no_bullets'] else "❌ Nee")
    col4.metric("Ban-List", "✅ Schoon" if not qa_final['ban_words_found'] else f"⚠️ Waarschuwing")

    st.markdown("---")
    st.markdown(final_json['body'])
    st.download_button("Download Markdown (.md)", final_json['body'], file_name=f"asset_{language_sel}.md", use_container_width=True)
