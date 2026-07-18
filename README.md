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

3. Créez un fichier `secrets.json` dans le même répertoire que ce script avec votre token de bot Discord :
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

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une Pull Request.
