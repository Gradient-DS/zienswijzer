# EU AI Act Risk Assessment — Zienswijzer

**Risk classification:** Limited risk.
**Date:** 2026-06-05
**Vendor:** Gradient.

## 1. AI system description
Zienswijzer uses a single AI component: a zero-shot text classifier
(`cross-encoder/nli-deberta-v3-small`, via HuggingFace `transformers`) that labels
stakeholder replies as "agrees to publish" or "objects to publication". The model
runs locally inside the deployment container; no inference data leaves the cluster.

## 2. Intended use
Assistive triage for human WOO case handlers. Output is a suggestion with a
confidence score; a human makes the publication decision.

## 3. Why "limited risk"
- Not a prohibited practice (Art. 5).
- Not high-risk (Annex III): it does not determine access to essential services,
  is not used in law enforcement decisioning, and has no legal effect on persons.
- It is an assistive classification tool with human oversight → limited risk, subject
  to transparency obligations (Art. 50).

## 4. Transparency (Art. 50)
Users are informed that classification is AI-generated. Labels and confidence
scores are surfaced in the UI; the candidate labels are fixed and documented.

## 5. Human oversight
Every classification is reviewable and overridable by the case handler. No
automated publication occurs based solely on the model output.

## 6. Data governance & residency
Inference runs in-cluster on EU infrastructure (data_residency: EU). No training
on user data is performed by this deployment. The base model is a fixed,
pre-trained, open model.

## 7. Robustness & monitoring
The classifier is loaded lazily and isolated to the `/classification` endpoints;
failures are surfaced as errors and do not affect core case management.
