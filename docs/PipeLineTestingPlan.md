# Pipeline Testing Plan

This document outlines the step-by-step testing process for each phase of the AI model seeding pipeline. Each phase is tested in isolation to ensure correctness before full automation.

---

## Phase 1: Extraction
- **Goal:** Ensure `scripts/ollama_data_extractor.py` generates raw model JSON files and logs missing tags.
- **Test:**
  1. Run the script.
  2. Check `data/raw/` for new model JSON files.
  3. Check `newly_missing_tags.txt` for any missing tags.

---

## Phase 2: Tag Mapping & Seeding
- **Goal:** Ensure all missing tags are identified and can be seeded.
- **Test:**
  1. Review `newly_missing_tags.txt` and copy its contents to `Tags/missing_tags.md`.
  2. Run `Tags/create_missing_tags.py`.
  3. Check `Tags/created_tag_ids.json` for new tag IDs and `Tags/created_tags_log.txt` for logs.

---

## Phase 3: Data Remapping (Model Mapping)
- **Goal:** Ensure all processed model files reference valid tag IDs and match the API schema.
- **Test:**
  1. Run `scripts/map_to_api.py` (or re-run `ollama_data_extractor.py` if it remaps).
  2. Check that all model files in `data/processed/` have valid tag IDs and required fields.

---

## Phase 4: Seeding Models
- **Goal:** Ensure models are seeded to the API and archived after success.
- **Test:**
  1. Run `scripts/seed_models.py`.
  2. Check `logs/seed_models_log.txt` for results.
  3. Confirm successfully seeded files are moved to `archive/`.

---

## Phase 5: Reporting & Cleanup
- **Goal:** Ensure logs and archives are correct and the process is traceable.
- **Test:**
  1. Review logs and archive contents.
  2. Confirm all steps are traceable and repeatable.
