# Bot AI Discord

Ce bot Discord est conçu pour aider les utilisateurs avec des tâches liées à l'intelligence artificielle, en particulier le traitement d'images et la résolution de problèmes.

## Fonctionnalités

- Extraire du texte à partir des images téléchargées sur Discord
- Améliorer la qualité des images avant le traitement
- Générer des réponses à des exercices mathématiques en utilisant g4f (sans clé API OpenAI)
- Formater et afficher le texte extrait dans les messages Discord

## Installation

1. Créer et activer un environnement virtuel Python :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Installez les dépendances requises :
    ```bash
    pip install -r requirements.txt
    ```
    Ce fichier inclut aussi les dépendances OCR (EasyOCR + PyTorch CPU) necessaires a la commande `.devoir`.

3. Créez un fichier `secrets.json` dans le même répertoire que ce script avec votre token de bot Discord (copiez `secrets.json.example` et remplacez le token) :
    ```json
    {
      "discord_bot_token": "Votre_TOKEN_BOT_ICI"
    }
    ```

## Utilisation

Pour démarrer le bot :
```
python commande_ai.py
```

Une fois en ligne, utilisez la commande suivante dans tout canal Discord où le bot a les permissions :
`.devoir`

Cela provoquera le bot à :
1. Demander une image ou un lien vers une image
2. Traiter l'image
3. Extraire le texte de l'image
4. Utiliser g4f pour générer des réponses à des exercices
5. Afficher les résultats sous forme de messages Discord formatés

## Tests

Les tests unitaires se trouvent dans `tests/`. Ils ne nécessitent ni token Discord ni EasyOCR :
```bash
pip install pytest pillow
python -m pytest tests/
```

La CI (GitHub Actions) exécute flake8, `compileall` et pytest à chaque push/PR.

## État du projet

Version 1.1.0 — les fonctionnalités décrites ci-dessus sont livrées.
Aucun ticket fonctionnel ouvert ; les mises à jour de dépendances sont automatisées par Renovate.

## Limites connues

- Le bot repose sur [`g4f`](https://github.com/xtekky/gpt4free) avec des providers gratuits non officiels (PollinationsAI, OperaAria, Perplexity, etc.). Aucun de ces providers n'est garanti stable : ils peuvent changer ou cesser de fonctionner sans préavis. Aucun token OpenAI n'est requis, mais la disponibilité des réponses IA en dépend.
- Le bot demande `discord.Intents.all()`. Certains intents sont **privilégiés** côté Discord (notamment *Message Content Intent*). Activez-les dans le [Portail développeur Discord](https://discord.com/developers/applications) si le bot ne reçoit pas le contenu des messages.

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une Pull Request.

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
