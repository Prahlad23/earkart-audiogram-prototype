# AI-Assisted Audiogram Prototype

## What this is
A prototype that takes pure tone audiometry threshold data and automatically:
- Calculates PTA, degree of hearing loss, and type (conductive/sensorineural/mixed)
- Generates the audiogram chart
- Drafts a generic diagnosis + recommendation for audiologist review

This is a draft-assist tool only — all output requires audiologist review before 
reaching a patient. No real patient data was used in building or testing this.

## How it works
1. `src/calculations.py` — clinical rule logic (PTA, degree, type classification)
2. `src/chart.py` — audiogram chart generation
3. `src/report.py` — diagnosis/recommendation text templates
4. `src/pipeline.py` — combines all three into one flow
5. `app.py` — Streamlit demo interface

## Running it
\`\`\`
pip install -r requirements.txt
streamlit run app.py
\`\`\`

## Testing
\`\`\`
pytest
\`\`\`
11 test cases covering normal, mild/moderate/severe/profound degrees, and 
conductive/sensorineural/mixed/asymmetric cases — all passing.

## Scope and limitations
- Built and validated using self-constructed test cases based on WHO/ASHA 
  clinical standards, not real patient data.
- Does not integrate with physical audiometer/tympanometer hardware — 
  takes threshold values as manual input.
- Recommendation text is template-based, not free-form AI generation, 
  to keep every output traceable to a specific rule.

## Suggested next phases (not built in this prototype)
- Integration with live audiometer/tympanometer hardware
- Validation against real, anonymized patient reports
- Compliance/regulatory review before any clinical use