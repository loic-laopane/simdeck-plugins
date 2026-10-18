# SimDeck Plugins – consignes

## Workflow Git
- Ne jamais pousser directement sur `main`.
- Chaque modification : branche dédiée → Pull Request vers `main` → review → corrections → merge une fois la CI verte.
- Claude merge lui-même la PR (sans demander) dès que la review est traitée et que la CI est verte.

## Règles
- Après toute modification d'un plugin : augmenter sa `version`, lancer `python tools/build_index.py`, commiter `index.json`.
- `python tools/build_index.py --check` doit passer (c'est ce que vérifie la CI).
- Les listes d'actions / conditions / touches de `tools/build_index.py` doivent suivre celles du logiciel (`simdeck/pc/simdeck_server/engine.py` et `keys.py`).
- Textes destinés aux utilisateurs en français.
