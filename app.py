from flask import Flask, render_template, request, jsonify
import spacy

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

CLAUSE_LIBRARY = {
    "nda": {
        "name": "Non-Disclosure Agreement",
        "sections": [
            "1. Purpose\nThe Parties wish to explore a potential business relationship and may exchange confidential and proprietary information for that purpose.",
            "2. Definition of Confidential Information\n\"Confidential Information\" means any technical, commercial or business information disclosed in any form that is marked or reasonably understood to be confidential.",
            "3. Confidentiality Obligations\nThe Receiving Party shall keep all Confidential Information strictly confidential, shall use it only for the Purpose and shall not disclose it to any third party without prior written consent of the Disclosing Party.",
            "4. Standard of Care\nThe Receiving Party shall protect the Confidential Information using at least the same degree of care it uses for its own confidential information and in no event less than a reasonable degree of care.",
            "5. Exclusions\nConfidential Information does not include information that is or becomes public through no fault of the Receiving Party, was already known without restriction, or is independently developed without reference to the Confidential Information.",
            "6. Term and Survival\nThe obligations under this Agreement start on the Effective Date and continue for three (3) years after the last disclosure of Confidential Information.",
            "7. Return or Destruction\nUpon written request, the Receiving Party shall promptly return or permanently destroy all copies of Confidential Information and confirm such destruction in writing.",
            "8. Remedies\nUnauthorised disclosure may cause irreparable harm. The Disclosing Party is entitled to seek injunctive relief in addition to any other remedies available at law or in equity.",
            "9. Governing Law\nThis Agreement shall be governed by and construed in accordance with the laws of India, without regard to conflict-of-law principles."
        ]
    },
    "employment": {
        "name": "Employment Agreement",
        "sections": [
            "1. Position\nThe Employee is engaged in the position described in the Schedule and shall perform the duties and responsibilities assigned by the Employer from time to time.",
            "2. Commencement and Term\nEmployment commences on the Start Date and continues until terminated in accordance with this Agreement.",
            "3. Working Hours and Location\nThe Employee shall work the standard working hours of the Employer. Remote or hybrid work arrangements, if any, shall be as mutually agreed in writing.",
            "4. Compensation\nThe Employee shall receive the salary and benefits set out in the Schedule, subject to deductions and statutory withholdings as required by law.",
            "5. Confidentiality and Intellectual Property\nAll work products, inventions and materials created in the course of employment are the exclusive property of the Employer. The Employee shall not disclose confidential information during or after employment.",
            "6. Leave and Holidays\nThe Employee is entitled to leave and holidays in accordance with the Employer’s policies and applicable law.",
            "7. Probation and Performance\nThe Employee may initially be placed on probation. Ongoing employment is subject to satisfactory performance and adherence to company policies.",
            "8. Termination\nEither Party may terminate this Agreement by giving written notice as specified in the Schedule or payment in lieu of such notice.",
            "9. Governing Law\nThis Agreement shall be governed by and construed in accordance with the laws of India."
        ]
    }
}

KEYWORD_RULES = {
    "startup": [
        "Additional Clause: In a startup context, the Parties acknowledge that products, business models and pricing may evolve and agree to cooperate in good faith to amend this Agreement if required."
    ],
    "remote": [
        "Additional Clause: Where work is performed remotely, the Receiving Party shall ensure secure connections, strong access controls and compliance with the information-security guidelines of the other Party."
    ],
    "intern": [
        "Additional Clause: Where the engagement relates to an intern, the primary objective is training and learning and any stipend or benefits shall be as specified in the Schedule."
    ]
}

def analyze(text):
    doc = nlp(text or "")
    return [(ent.text, ent.label_) for ent in doc.ents]

def build_header(doc_type, entities):
    base_name = CLAUSE_LIBRARY[doc_type]["name"]

    org_list = []
    person_list = []
    place_list = []

    for text, label in entities:
        if label == "ORG":
            t = text.strip()
            tl = t.lower()
            if tl not in ("nda", "non-disclosure agreement", "agreement"):
                org_list.append(t)
        elif label == "PERSON":
            person_list.append(text.strip())
        elif label in ("GPE", "LOC"):
            place_list.append(text.strip())

    party_a = org_list[0] if org_list else None
    party_b = person_list[0] if person_list else None
    place = place_list[0] if place_list else None

    if party_a is None:
        party_a = "Party A"
    if party_b is None:
        party_b = "Party B"
    if place is None:
        place = "India"

    header = (
        f"{base_name}\n\n"
        f'This {base_name} ("Agreement") is made between {party_a} and {party_b}. '
        f"This Agreement shall be governed by the laws of {place}."
    )
    return header


def generate_document(doc_type, text):
    entities = analyze(text)
    base = CLAUSE_LIBRARY[doc_type]
    sections = base["sections"][:]
    lower_text = (text or "").lower()
    used_keywords = []
    for key, extra_list in KEYWORD_RULES.items():
        if key in lower_text:
            used_keywords.append(key)
            for clause in extra_list:
                if clause not in sections:
                    sections.append(clause)
    header = build_header(doc_type, entities)
    body = "\n\n".join(sections)
    draft = header + "\n\n\n" + body
    return draft, entities, used_keywords, len(used_keywords)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json()
    doc_type = data.get("docType", "nda")
    text = data.get("requirements", "")
    draft, entities, keys, count = generate_document(doc_type, text)
    return jsonify({
        "draft": draft,
        "entities": entities,
        "keywords": keys,
        "adaptive_count": count
    })

if __name__ == "__main__":
    app.run(debug=True)
