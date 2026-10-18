# SimDeck – Plugins

Catalogue officiel des plugins du **Store SimDeck**. Le logiciel PC [SimDeck](https://github.com/loic-laopane/simdeck) lit `index.json` dans ce dépôt, puis télécharge un plugin quand l'utilisateur l'installe. Ajouter ou corriger un plugin ne demande donc aucune nouvelle version du logiciel.

## Organisation

```
games/simulation/racing/<id>/plugin.json   Sim racing (jeux et commandes communes)
games/simulation/flight/<id>/plugin.json   Flight sim
streaming/<id>/plugin.json                 Streaming & vidéo (OBS, Streamlabs…)
social/<id>/plugin.json                    Réseaux sociaux
system/<id>/plugin.json                    Windows
apps/<id>/plugin.json                      Applications
other/<id>/plugin.json                     Autres
index.json                                 Liste de tous les plugins (générée)
tools/build_index.py                       Validation + génération de l'index
```

Le nom du dossier est l'identifiant du plugin, et le dossier parent détermine sa catégorie. Un dossier `images/` peut contenir une image par touche (`<id de touche>.png` ou `.webp`, et `<id>@active.png` pour l'état actif ; 128×128 conseillé, 256×256 maximum). Voir [CONTRIBUTING.md](CONTRIBUTING.md#images-des-touches).

## Plugins disponibles

| Catégorie | Plugins |
|-----------|---------|
| Sim racing | Commandes communes, iRacing, Le Mans Ultimate, Automobilista 2, Assetto Corsa, ACC, Assetto Corsa EVO, Assetto Corsa Rally, KartKraft, Project Motor Racing, rFactor 2, F1 24 |
| Flight sim | Commandes communes, MSFS 2020, MSFS 2024, X-Plane 12, DCS World |
| Streaming & vidéo | OBS Studio, Streamlabs Desktop, NVIDIA |
| Réseaux sociaux | YouTube, Twitch, Instagram, TikTok, X, Facebook, Kick, Reddit |
| Windows | Son, multimédia, outils système, alimentation |
| Applications | Outils sim racing (SimHub, Crew Chief, Steam, Discord, Spotify), Bureautique, Création & navigateurs |

## Ajouter un plugin

Voir [CONTRIBUTING.md](CONTRIBUTING.md).
