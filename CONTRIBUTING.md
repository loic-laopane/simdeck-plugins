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
| `requires` | Plugins dont les presets sont réutilisés (`"plugin/preset"` dans les boards) ; ils sont installés automatiquement. Un plugin requis ne peut pas lui-même avoir de `requires` (une seule profondeur) |
| `default` | Réservé aux plugins de base `simracing`, `flightsim` et `windows` (installés au premier lancement) |
| `presets[]` | Champs d'une touche : `label`, `icon`, `image`, `color`, `textColor`, `actions`, `longPressActions`, `releaseActions`, `activeWhen`, `activeStyle`, `description` |

Les actions possibles : `hotkey`, `text`, `launch`, `open`, `command`, `kill`, `focus`, `delay`, `waitUntil`, `switchPage`, `variable`, `if`, `repeat`, `stop`, `iracingPit`, `iracingChat`.
Les conditions possibles (`activeWhen`, `if`, `waitUntil`) : `always`, `processRunning`, `windowFocused`, `variable`, `not`, `and`, `or`.

Les noms de touches s'écrivent en minuscules : `a`–`z`, `0`–`9`, `f1`–`f24`, `ctrl`, `shift`, `alt`, `win`, `rctrl`, `rshift`, `ralt`, `enter`, `esc`, `tab`, `space`, `backspace`, `delete`, `insert`, `home`, `end`, `pageup`, `pagedown`, `up`, `down`, `left`, `right`, `num0`–`num9`, `numadd`, `numsubtract`, `nummultiply`, `numdivide`, `numdecimal`, `numenter`, `volumeup`, `volumedown`, `volumemute`, `mediaplaypause`, `medianext`, `mediaprev`, `mediastop`… (liste complète dans `tools/build_index.py`).

La CI vérifie aussi qu'un plugin modifié a bien une `version` supérieure à celle de `main`.

## Images des touches

Chaque touche d'un plugin peut avoir une image, rangée dans le dossier `images/` du plugin et nommée d'après l'identifiant de la touche :

```
streaming/obs/plugin.json
streaming/obs/images/stream_start.png          image de la touche « stream_start »
streaming/obs/images/stream_start@active.png   (facultatif) image quand la touche est « active »
```

| Règle | |
|-------|--|
| Format | PNG ou WebP (transparence conseillée) |
| Taille conseillée | **128×128 px** : une image plus petite est acceptée (avertissement), mais moins nette |
| Taille maximale | **256×256 px** : au-delà, la CI refuse l'image |
| Poids maximal | 256 Ko |

Une touche sans image garde son emoji. Les images sont listées dans `index.json` avec leur empreinte SHA-256, et SimDeck les vérifie au téléchargement. Ajouter, modifier ou supprimer une image compte comme une modification du plugin : **augmentez sa `version`**.

L'utilisateur peut remplacer n'importe quelle image par la sienne dans SimDeck (*Store → plugin → Personnaliser les images*) : son image passe avant celle du plugin.

## Schéma de touches SimDeck

Pour un jeu, utilisez des touches absentes des claviers afin d'éviter les conflits :

| Usage | Touches |
|-------|---------|
| Sim racing | `f13`–`f24`, `ctrl+f13`–`f24`, `shift+f13`–`f24` (voir `simracing`) |
| Flight sim | `alt+f13`–`f24`, `ctrl+shift+f13`–`f24` (voir `flightsim`) |
| Streaming | `ctrl+alt+f13`… |

Réutilisez de préférence les presets des plugins communs (`simracing/...`, `flightsim/...`) : l'utilisateur n'associe ses touches qu'une seule fois.

## Sécurité

Un plugin peut lancer des programmes ou des commandes sur le PC. Chaque Pull Request est relue : pas de commande destructrice sans appui long, pas de téléchargement ni de script obscur. Le Store affiche à l'utilisateur ce qu'un plugin est capable de faire (lancer des programmes, ouvrir des liens, exécuter des commandes, fermer des programmes, taper du texte). Une séquence qui contourne cet affichage (par exemple `win+r` puis un texte de commande) est refusée en review.
