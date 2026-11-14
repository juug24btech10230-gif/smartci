# smartci

Small Python shop app (pricing, cart, inventory) used to practise CI/CD automation.

| Folder | Purpose |
|---|---|
| `src/`, `tests/` | App code and pytest suite |
| `.github/workflows/ci.yml` | Baseline CI (Lab 2) |
| `.github/workflows/smart-ci.yml` | Cache invalidation, test routing, risk prediction, log summary |
| `scripts/smart_cache.py` | Smart build-cache invalidation using the import graph |
| `scripts/select_tests.py` | Dynamic test-subset routing from `git diff` |
| `scripts/summarize_log.py` | LLM / rule-based build-log summarizer |
| `ml/` | Build-failure prediction (dataset, training, prediction) |

## Run locally
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt scikit-learn pandas
pytest -v
python scripts/smart_cache.py
python scripts/select_tests.py --files src/pricing.py
python ml/make_dataset.py && python ml/train.py && python ml/predict.py
```
Set `ANTHROPIC_API_KEY` as a repo secret to enable the LLM summary; without it the
summarizer uses a rule-based fallback.
