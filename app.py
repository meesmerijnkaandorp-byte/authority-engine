import streamlit as st
from openai import OpenAI
import time
import re
import json

# --- CONFIGURATIE ---
st.set_page_config(page_title="Authority Engine v47.0 | The Uncompromised", layout="wide")

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

# Uitgebreide, native-level taalinstructies
LANG_INSTRUCTIONS = {
    "NL": "Schrijf het volledige artikel uitsluitend in professioneel, idiomatisch Nederlands op moedertaalniveau. Gebruik een vloeiende, natuurlijke en overtuigende schrijfstijl. Vermijd letterlijk vertaalde formuleringen en onnatuurlijke woordkeuze.",
    "EN": "Write the full article exclusively in professional, idiomatic English at native level. Use a smooth, natural, expert, and persuasive writing style. Avoid translation-like wording and unnatural phrasing.",
    "DE": "Schreiben Sie das vollständige Artikel ausschließlich in professionellem, idiomatischem Deutsch auf Muttersprachniveau. Verwenden Sie einen fließenden, natürlichen und überzeugenden Schreibstil. Vermeiden Sie wörtliche Übersetzungen.",
    "FR": "Écrivez l'article exclusivement en français professionnel et idiomatique de niveau langue maternelle. Utilisez un style d'écriture fluide, naturel et convaincant. Évitez les formulations littérales."
}

UNIVERSAL_BAN = [
    "oase", "essentieel", "cruciaal", "wereld van verschil", "esthetiek", "harmonie", "samenspel", 
    "paradigma", "fundamenteel", "belangrijkste rol", "stel je voor", "in de moderne wereld", 
    "niet alleen ... maar ook", "ultieme", "ongeëvenaard", "tegenwoordig", "meer dan ooit"
]

TOV_PROFILES = {
    "Expert/Adviserend": {
        "instructie": "Schrijf als een doorgewinterde, onafhankelijke expert. Geef direct, concreet en praktisch advies gebaseerd op harde feiten. De lezer zoekt autoriteit, geen gezelligheid. Wees stellig maar genuanceerd. Noem afmetingen, specifieke materialen, en harde vuistregels. Vermijd filosofische bespiegelingen.",
        "ban": UNIVERSAL_BAN + ["gezelligheid", "sfeervol", "beleving", "droom", "magisch", "knus"]
    },
    "Verhalend/Lifestyle": {
        "instructie": "Schrijf nuchter, beschouwend en verhalend, maar blijf met beide benen op de grond. Gebruik de 'zaterdagmorgen-energie': herkenbare, fysieke details in het dagelijks leven. Vermijd abstracte marketingtaal. Maak de tekst tastbaar door zintuiglijke details (gewicht, geluid, textuur) te benoemen.",
        "ban": UNIVERSAL_BAN + ["synergie", "optimaliseren", "implementeren", "efficiëntie"]
    },
    "Zakelijk/Technisch": {
        "instructie": "Schrijf professioneel, analytisch, B2B-gericht en objectief. Focus op harde specificaties, kosten, ROI, duurzaamheid in productie en praktische bruikbaarheid voor professionals. De tekst moet klinken als een whitepaper of een vakblad.",
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

# --- ONGECOMPROMITTEERDE SYSTEM PROMPTS (v47.0) ---

STRATEGIST_SYSTEM = """Jij bent een Meesterlijke Content Architect en Hoofdredacteur. Je ontwerpt hoogwaardige, redactionele artikelen die mijlenver uitstijgen boven standaard SEO-content.
Jouw doel is om een feilloze, psychologische brug te slaan tussen de niche van de publisher en de uiteindelijke commerciële behoefte van de lezer.

TAAL: {language_instruction}
TONE OF VOICE: {tov_instruction}
INTENTIE VAN HET ARTIKEL: {intent_tone}

JOUW TAKEN EN REGELS:
1. DE USE-CASE BRUG: Bouw geen theorie, maar een contextueel gebruiksmoment. Hoe gebruikt de lezer van {publisher_info} het product ({anchor}) fysiek in de praktijk? Verbind de sfeer van de publisher logisch aan het gebruik van het product.
2. EXPERT DATA: Bedenk per hoofdstuk 3 snoeiharde, concrete datapunten, vuistregels, afmetingen of materiaalkenmerken. Vermijd open deuren ("comfort is belangrijk"). Geef antwoorden ("kies een zithoogte van 45cm").
3. STRUCTUUR: Plan 4 tot 5 secties. Iedere sectie behandelt een UNIEK aspect. Geen herhaling van de conclusie in eerdere secties.
4. KOPPEN FORMAT: Gebruik uitsluitend 'Sentence case' voor alle koppen (Alleen het allereerste woord krijgt een hoofdletter). Geef de koppen actiegerichte en specifieke titels, vermijd abstracte termen.
5. FORMAT: Je levert UITSLUITEND een geldig JSON object.

SCHEMA:
{{
  "title": "Sterke, redactionele kop (Sentence case)",
  "use_case_bridge": "Jouw psychologische en praktische brug tussen publisher en product.",
  "sections": [
    {{ 
      "h2": "Specifieke tussenkop in sentence case", 
      "key_points": ["Hard feit 1", "Diepgaand inzicht 2", "Vuistregel 3"],
      "friction": "Welk specifiek, herkenbaar probleem lossen we hier op?"
    }}
  ]
}}"""

WRITER_SYSTEM = """Jij bent een Award-Winning Senior Vakjournalist. Je schrijft teksten die publicatie-klaar zijn voor premium platformen.
Je weigert generieke AI-taal ("fluff") te gebruiken en vult je tekst uitsluitend met waarde, details en expertise.

TAAL: {language_instruction}
STIJL: {tov_instruction} 
FOCUS: {intent_tone}

JOUW SCHRIJFWETTEN (NEGEER DEZE NOOIT):
1. VLOEIEND EN MENSELIJK: Gebruik een rijke, gevarieerde zinsopbouw. Schrijf met de "zaterdagmorgen-energie": nuchter, tastbaar en direct.
2. ABSOLUUT VERBOD OP OPSOMMINGEN: Gebruik GEEN ENKELE bulletpoint, geen streepjes en geen genummerde lijsten. Alles moet worden geschreven in samenhangende, lopende alinea's. 
3. GEEN WOLLIGE INLEIDINGEN: Vermijd zinnen als "In de wereld van vandaag..." of "Stel je voor...". Val direct met de deur in huis met een observatie of feit.
4. GEEN MINI-CONCLUSIES: Sluit je hoofdstuk niet af met een samenvatting (zoals "Kortom, let goed op je keuze"). Rond je alinea af en stop.
5. GEBRUIK DE DATA: Verwerk de meegeleverde 'key_points' op een natuurlijke, redactionele manier in de tekst. Laat zien dat je de expert bent.
6. VERBODEN WOORDEN: Vermijd koste wat kost de volgende termen: {ban_list}.

Schrijf uitsluitend de tekst voor het aangegeven hoofdstuk. Gebruik Markdown voor de H2 kop en maak **kernwoorden** incidenteel vetgedrukt voor scannability."""

EDITOR_SYSTEM = """Jij bent de Meedogenloze Eindredacteur en Assembleur. Jij bent de laatste kwaliteitscontroleur voordat het artikel naar de drukker gaat.
Je levert UITSLUITEND JSON.

TAAL: {language_instruction}
VERBODEN WOORDEN CHECK: Zorg dat deze woorden NOOIT in de tekst voorkomen: {ban_list}.

JOUW TAKEN (ABSOLUTE PRIORITEIT):
1. NIET SAMENVATTEN OF INKORTEN: Plak de aangeleverde hoofdstukken integraal aan elkaar. Jouw doel is een LANG en VOLLEDIG artikel van circa {target} woorden. Vernietig geen werk van de schrijver.
2. KOPPEN CONTROLE: Controleer streng of alle koppen (H1 en H2) in 'Sentence case' staan. Er mogen GEEN Koppen Zijn Waarbij Elk Woord Een Hoofdletter Heeft.
3. BULLET-SWEEP: Als de schrijver per ongeluk toch een bulletpoint (-) of opsomming heeft gemaakt, schrijf jij deze subiet om naar een lopende, grammaticale alinea.
4. DE ANKERTEKST CHIRURGIE ({mode}): Je plaatst EXACT ÉÉN KEER de marker [ANCHOR_SPOT] in de tekst, bedoeld voor de term '{anchor}'.
   - Bij 'Exact Match': De tekst eromheen MOET zich plooien naar de ankertekst, niet andersom. Als het anker een infinitief is (bijv. 'eetkamerstoel kopen'), gebruik dan vluchtstrook-sjablonen zoals: "Wanneer je overweegt tot [ANCHOR_SPOT]...", "In het proces van [ANCHOR_SPOT] merken we dat...", of "Wie zoekt naar [ANCHOR_SPOT] moet letten op...". De zin moet 100% foutloos Nederlands zijn.
   - Bij 'Natuurlijk/Vloeiend': Verbuig het anker, maak het meervoud of voeg lidwoorden toe zodat het onzichtbaar opgaat in de flow.
5. DE FINALE CONCLUSIE: Voeg aan het einde van de body een gloednieuwe, krachtige laatste alinea toe die het artikel samenvat met een helder (koop)advies.

VOORDAT JE DE BODY SCHRIJFT:
Vul het veld `anchor_sentence_check` in met de geplande zin waarin de ankertekst voorkomt en beoordeel zelf kritisch of deze zin grammaticaal perfect is.

SCHEMA:
{{
  "title": "Definitieve kop in sentence case", 
  "meta": "SEO-geoptimaliseerde meta description van max 155 tekens", 
  "slug": "url-slug-in-kebab-case", 
  "anchor_sentence_check": "Schrijf de zin met de [ANCHOR_SPOT] hier uit en valideer de grammatica.",
  "body": "## Tussenkop\\n\\nVolledige, ongecensureerde tekst van hoofdstuk 1...\\n\\n## Volgende kop\\n\\nVolledige tekst van hoofdstuk 2, met precies één [ANCHOR_SPOT]..."
}}"""

RETRY_EDITOR_SYSTEM = """Jij bent de Strenge Eindredacteur. JE VORIGE WERK WERD AFGEKEURD DOOR DE QA SYSTEMEN.
Je hebt waarschijnlijk de tekst drastisch samengevat (te kort), bulletpoints gebruikt, of verboden woorden (zoals essentieel/cruciaal) laten staan.

HERSTELOPDRACHT:
1. Neem de originele teksten en plak ze aan elkaar zonder ze in te korten! Het artikel moet lang en diepgaand zijn.
2. Herschrijf elke opsomming naar lopende zinnen.
3. Gebruik 'Sentence case' voor alle koppen.
4. Plaats de [ANCHOR_SPOT] in een foutloze zin.
5. Vermijd deze woorden absoluut: {ban_list}.

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
st.title("🛡️ Authority Engine v47.0")
st.caption("The Uncompromised Engine | Maximale instructie-diepte voor superieure output")

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
        st.write("📐 Fase 1: Diepgaande Blueprint genereren...")
        strat_sys = STRATEGIST_SYSTEM.format(
            language_instruction=lang_inst,
            tov_instruction=current_tov["instructie"],
            intent_tone=intent_tone,
            publisher_info=publisher_info, 
            anchor=anchor_text
        )
        blueprint = json.loads(clean_json_string(call_ai(strat_sys, f"Ontwerp het artikel. Target: {dynamic_target}w", json_mode=True)))

        st.info(f"🌉 **Bedachte Brug:** {blueprint.get('use_case_bridge', 'Niet gevonden')}")

        # 2. WRITER
        st.write("🖋️ Fase 2: Schrijven met maximale detail-dwang...")
        full_draft = ""
        sec_target = dynamic_target // max(1, len(blueprint.get("sections", [1,2,3,4])))
        
        for section in blueprint.get("sections", []):
            write_sys = WRITER_SYSTEM.format(
                language_instruction=lang_inst, tov_instruction=current_tov["instructie"], 
                intent_tone=intent_tone, ban_list=ban_list_str
            )
            write_prompt = f"Kop: {section.get('h2')}\nData Punten om te verwerken: {', '.join(section.get('key_points', []))}\nFrictie: {section.get('friction')}\nTarget: {sec_target}w."
            draft = call_ai(write_sys, write_prompt)
            full_draft += f"\n\n## {section.get('h2')}\n{draft}"

        # 3. EDITOR
        st.write("✨ Fase 3: Assembleren (Met strikt verbod op inkorten!)...")
        editor_sys = EDITOR_SYSTEM.format(
            language_instruction=lang_inst, target=dynamic_target, anchor=anchor_text, 
            mode=anchor_mode, ban_list=ban_list_str
        )
        raw_editor = call_ai(editor_sys, f"Assembleer dit exact, integreer [ANCHOR_SPOT] en voeg de eindconclusie toe:\n{full_draft}", json_mode=True)
        final_json = json.loads(clean_json_string(raw_editor))

        # --- QA & RETRY ---
        qa_result = validate_output(final_json.get("body", ""), target_url, current_tov["ban"])
        word_count_check = count_words(final_json.get("body", ""))
        
        if (not qa_result["no_bullets"] or qa_result["ban_words_found"] or word_count_check < (dynamic_target * 0.5)) and CONFIG["ENABLE_RETRY_ON_QA_FAIL"]:
            st.warning(f"⚠️ QA Faalde (Bullets, Ban-words of veel te kort: {word_count_check}w). Strenge Retry wordt gestart...")
            retry_sys = RETRY_EDITOR_SYSTEM.format(lang_code=language_sel, ban_list=ban_list_str)
            raw_retry = call_ai(retry_sys, f"Hier is de originele ruwe tekst. Maak hier een LANG en FOUTLOOS eindproduct van:\n{full_draft}", temp=0.4, json_mode=True)
            final_json = json.loads(clean_json_string(raw_retry))
            st.success("✅ Retry afgerond.")

        # 4. PYTHON LINK INJECTION
        body = final_json.get("body", "")
        if "[ANCHOR_SPOT]" in body:
            body = body.replace("[ANCHOR_SPOT]", f"[{anchor_text}]({target_url})", 1)
            body = body.replace("[ANCHOR_SPOT]", anchor_text)
        else:
            pattern = re.compile(re.escape(anchor_text), re.IGNORECASE)
            body = pattern.sub(f"[{anchor_text}]({target_url})", body, count=1)
        
        final_json["body"] = cleanup_text(body)
        
        qa_final = validate_output(final_json['body'], target_url, current_tov["ban"])
        if not qa_final["link_present"]:
            st.error("Kritieke fout: Ankertekst kon niet worden geplaatst.")
        
        status.update(label=f"✅ Content Ready in {int(time.time() - start_time)}s", state="complete")

    # --- OUTPUT ---
    st.header(final_json.get('title'))
    
    col1, col2, col3, col4 = st.columns(4)
    final_wc = count_words(final_json['body'])
    col1.metric("Volume", f"{final_wc} w", delta=final_wc - dynamic_target)
    col2.metric("Link", "✅ Aanwezig" if qa_final["link_present"] else "❌ Ontbreekt")
    col3.metric("Bullet-Vrij", "✅ Ja" if qa_final['no_bullets'] else "❌ Nee")
    col4.metric("Ban-List", "✅ Schoon" if not qa_final['ban_words_found'] else f"❌ Fout ({len(qa_final['ban_words_found'])})")

    st.info(f"🔍 **AI Grammatica Check:** {final_json.get('anchor_sentence_check', 'Niet gevonden')}")

    st.markdown("---")
    st.markdown(final_json['body'])
    st.download_button("Download Markdown (.md)", final_json['body'], file_name=f"asset_{language_sel}.md", use_container_width=True)
