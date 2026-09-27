# Clinical Emergency Triage Protocol & Pharmacology Decision Matrix
**Document ID:** MED-TRIAGE-2026-CLIN  
**Classification:** Clinical Reference Standard - Hospital Systems  
**Author:** Department of Emergency Medicine & Acute Care Pharmacotherapy  
**Effective Date:** 2026-02-01  
**Version:** 3.4.1  

---

## 1. Emergency Severity Index (ESI) Triage Classification
The Emergency Severity Index (ESI) is a validated 5-level triage algorithm used to stratify patient acuity, determine resuscitation priority, and optimize emergency department resource allocation.

### 1.1 Triage Stratification Levels
1. **ESI Level 1 (Resuscitation - Immediate Life Threat):**
   - Definition: Patient requires immediate life-saving intervention without delay.
   - Clinical Presentation: Cardiac arrest, respiratory arrest, severe anaphylaxis with airway compromise, massive exsanguinating hemorrhage, unresponsive coma (Glasgow Coma Scale GCS <= 8).
   - Time to Physician Evaluation: 0 minutes (Immediate intervention).
2. **ESI Level 2 (Emergent - High Risk / Confused / Severe Distress):**
   - Definition: High-risk situation, new-onset lethargy or acute confusion, or severe pain/distress (Pain scale >= 7/10).
   - Clinical Presentation: Suspected Acute Coronary Syndrome (ACS) with retrosternal chest pressure radiating to left jaw, acute stroke symptoms within 4.5-hour thrombolysis window (BE-FAST positive), ectopic pregnancy with severe abdominal tenderness, systemic sepsis meeting SIRS criteria.
   - Time to Physician Evaluation: <= 10 minutes.
3. **ESI Level 3 (Urgent - Stable Vitals, Multi-Resource Need):**
   - Definition: Patient requires two or more diagnostic or therapeutic hospital resources (e.g., intravenous fluids + contrast CT scan + laboratory blood draw).
   - Physiological Guardrails: Heart Rate 60-100 bpm, Respiratory Rate 12-20 bpm, SpO2 >= 92% on ambient air, Systolic BP >= 100 mmHg.
4. **ESI Level 4 (Less Urgent - Single Resource):**
   - Definition: Requires exactly one diagnostic resource (e.g., plain extremity X-ray or simple laceration suture).
5. **ESI Level 5 (Non-Urgent - Zero Resources):**
   - Definition: Clinical evaluation only with prescription renewal or suture removal; no imaging or IV therapy required.

---

## 2. Acute Coronary Syndrome (ACS) Pharmacotherapy Protocol
When a patient presents with symptoms suggestive of ST-Elevation Myocardial Infarction (STEMI) or Non-ST-Elevation Myocardial Infarction (NSTEMI):

### 2.1 Immediate Therapeutic Regimen
- **Aspirin (Acetylsalicylic Acid):**
  - Dose: 324 mg chewable, non-enteric coated tablet administered immediately upon triage arrival.
  - Mechanism: Irreversible cyclooxygenase-1 (COX-1) inhibition preventing thromboxane A2 synthesis and platelet aggregation.
  - Contraindication: Active anaphylaxis to salicylates or acute, uncontrolled gastrointestinal hemorrhage.
- **P2Y12 Receptor Antagonist (Dual Antiplatelet Therapy - DAPT):**
  - Option A (Ticagrelor): 180 mg oral loading dose, followed by 90 mg BID maintenance.
  - Option B (Clopidogrel): 600 mg oral loading dose if urgent CABG surgery cannot be excluded.
- **Anticoagulation:**
  - Unfractionated Heparin (UFH): IV bolus 60 units/kg (max 4,000 units), followed by continuous infusion at 12 units/kg/hr (max 1,000 units/hr), titrated to target activated partial thromboplastin time (aPTT) of 50-70 seconds.
  - Enoxaparin (LMWH): 30 mg IV bolus plus 1 mg/kg subcutaneous injection every 12 hours (adjust dose for renal clearance CrCl < 30 mL/min to 1 mg/kg once daily).

---

## 3. Sepsis & Septic Shock Early Resuscitation Bundle
Adheres to the Surviving Sepsis Campaign 1-Hour Bundle guidelines.

### 3.1 Time-Zero Intervention Sequence
1. **Lactate Measurement:** Measure serum lactate immediately via point-of-care venous/arterial blood gas. Re-measure within 2-4 hours if initial lactate > 2.0 mmol/L.
2. **Blood Cultures:** Obtain 2 sets of peripheral blood cultures (aerobic and anaerobic) prior to initiating antimicrobial therapy. Do not delay antibiotic administration by > 45 minutes if venipuncture is difficult.
3. **Broad-Spectrum Antibiotics:** Administer IV empiric antibiotic within 60 minutes of sepsis identification (e.g., Vancomycin 15-20 mg/kg IV + Cefepime 2g IV or Piperacillin-Tazobactam 4.5g IV).
4. **Fluid Resuscitation:** Administer 30 mL/kg of IV balanced crystalloid (Lactated Ringer's solution) within 3 hours for hypotension (Mean Arterial Pressure MAP < 65 mmHg) or serum lactate >= 4.0 mmol/L.
5. **Vasopressor Support:** If MAP remains < 65 mmHg despite crystalloid bolus, initiate Norepinephrine infusion at 2-5 mcg/min, titrated rapidly to achieve MAP >= 65 mmHg. Vasopressin at fixed 0.03 units/min may be added as second-line agent.

---

## 4. Patient Privacy, HIPAA & Audit Trail Requirements
- In compliance with HIPAA Security Rule 45 CFR Part 160/164, Protected Health Information (PHI) including Medical Record Numbers (MRN), names, and birth dates must be de-identified or encrypted using FIPS 140-3 approved cryptography.
- Clinical Decision Support (CDS) logs must record doctor NPI, timestamp, overrides, and medication dosages with tamper-evident SHA-256 audit hashing.
