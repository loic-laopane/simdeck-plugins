# Contribuer un plugin

1. Créez le dossier `<catégorie>/<id>/` (par exemple `games/simulation/racing/mon-jeu/`) avec un fichier `plugin.json`.
2. Lancez `python tools/build_index.py` : le plugin est validé et `index.json` est régénéré.
3. Ouvrez une Pull Request avec le plugin **et** l'`index.json` mis à jour. La CI refuse un plugin invalide ou un index pas à jour.

## Format de `plugin.json`

```json
{
  "id": "mon-jeu",
  "name": "Mon jeu",
  "version": "1.0.0",
  "minAppVersion": "1.1.0",
  "author": "Votre nom",
  "category": "simracing",
  "icon": "🏎️",
  "color": "#1E88E5",
  "description": "Touches et page pour Mon jeu.",
  "notes": ["Associez les touches dans Options → Contrôles."],
  "requires": ["simracing"],
  "autoSwitch": { "processName": "MonJeu.exe" },
  "presets": [
    {
      "id": "launch", "label": "Lancer Mon jeu", "icon": "🏎️", "color": "#1E88E5",
      "description": "Lance le jeu via Steam.",
      "actions": [{ "type": "open", "target": "steam://rungameid/123456" }],
      "activeWhen": { "type": "processRunning", "processName": "MonJeu.exe" },
      "activeStyle": { "color": "#43A047" }
    }
  ],
  "boards": [
    {
      "id": "main", "name": "Mon jeu", "rows": 2, "cols": 3,
      "buttons": [
        { "preset": "launch", "row": 0, "col": 0 },
        { "preset": "simracing/pit_limiter", "row": 0, "col": 1 }
      ]
    }
  ]
}
```

| Champ | Règle |
|-------|-------|
| `id` | Égal au nom du dossier : minuscules, chiffres, `-`, `_` |
| `version` | `MAJEUR.MINEUR.CORRECTIF`. **Augmentez-la à chaque modification** : c'est ce qui affiche « Mise à jour disponible » dans le Store |
| `minAppVersion` | Version minimale de SimDeck (pour un plugin qui utilise une action récente) |
| `category` | Imposée par le dossier |
| `requires` | Plugins dont les presets sont réutilisés (`"plugin/preset"` dans les boards) ; ils sont installés automatiquement |
| `default` | Réservé aux plugins de base installés au premier lancement |
| `presets[]` | Champs d'une touche : `label`, `icon`, `image`, `color`, `textColor`, `actions`, `longPressActions`, `releaseActions`, `activeWhen`, `activeStyle`, `description` |

Les actions possibles : `hotkey`, `text`, `launch`, `open`, `command`, `kill`, `focus`, `delay`, `waitUntil`, `switchPage`, `variable`, `if`, `repeat`, `stop`, `iracingPit`, `iracingChat`.

## Schéma de touches SimDeck

Pour un jeu, utilisez des touches absentes des claviers afin d'éviter les conflits :

| Usage | Touches |
|-------|---------|
| Sim racing | `F13`–`F24`, `Ctrl+F13`–`F24`, `Maj+F13`–`F24` (voir `simracing`) |
| Flight sim | `Alt+F13`–`F24`, `Ctrl+Maj+F13`–`F24` (voir `flightsim`) |
| Streaming | `Ctrl+Alt+F13`… |

Réutilisez de préférence les presets des plugins communs (`simracing/...`, `flightsim/...`) : l'utilisateur n'associe ses touches qu'une seule fois.

## Sécurité

Un plugin peut lancer des programmes ou des commandes sur le PC. Chaque Pull Request est relue : pas de commande destructrice sans appui long, pas de téléchargement ni de script obscur. Le Store affiche à l'utilisateur ce qu'un plugin est capable de faire (lancer des programmes, ouvrir des liens, exécuter des commandes, fermer des programmes).
