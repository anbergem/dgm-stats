# Disc Golf Metrix Stats
Head over to [dgmstats.golf](https://dgmstats.golf) to check out the live version.

## Pre-installation requirements
Find your DGM code at the bottom of [this page](https://discgolfmetrix.com/?u=account_edit).
It's just called `Code`.
```shell
echo 'DGM_CODE=<your-dgm-code>' > .env
```

## Installation
Install [poetry](https://python-poetry.org).
```shell
poetry install
poetry run streamlit run dgm_stats/app/app.py
```