import discord
import asyncio
import json
import requests
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from discord.ext import commands
from g4f.client import AsyncClient as AIAsyncClient

# Providers g4f essayes en priorite pour eviter toute cle API.
NO_KEY_PROVIDERS = [
    "PollinationsAI",
    "OperaAria",
    "Perplexity",
    "Qwen",
    "WeWordle",
    "TeachAnything",
]

IMAGE_FETCH_TIMEOUT = 15
MAX_IMAGE_BYTES = 10 * 1024 * 1024

_EASYOCR_READER = None

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=".", intents=intents)


@client.event
async def on_ready():
    print("Le bot est en ligne")
    await client.change_presence(activity=discord.Game(name=".help"))


def _get_easyocr_reader():
    global _EASYOCR_READER
    try:
        import easyocr
    except ModuleNotFoundError:
        raise

    # Le chargement des modeles OCR est lourd: on le fait une seule fois.
    if _EASYOCR_READER is None:
        _EASYOCR_READER = easyocr.Reader(["fr"], gpu=False)
    return _EASYOCR_READER


# Fonction pour extraire le texte d'une image
def extract_text_from_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        reader = _get_easyocr_reader()

        # Extrait le texte
        result = reader.readtext(np.array(img))

        # Rassemble le texte extrait
        extracted_text = " ".join([item[1] for item in result])

        return extracted_text

    except ModuleNotFoundError:
        return (
            "EasyOCR n'est pas installe. Executez: "
            "pip install easyocr torch==2.5.1+cpu torchvision==0.20.1+cpu "
            "--extra-index-url https://download.pytorch.org/whl/cpu"
        )

    except Exception as e:
        print(f"Erreur lors de l'extraction du texte : {str(e)}")
        return "Une erreur s'est produite lors de l'extraction du texte."


async def generate_ai_answer(prompt_text):
    last_error = None

    for provider_name in NO_KEY_PROVIDERS:
        try:
            ai_client = AIAsyncClient(provider=provider_name)
            response = await ai_client.chat.completions.create(
                model="",
                messages=[
                    {
                        "role": "user",
                        "content": "Repondez aux exercices ou questions qui suivent : " + prompt_text,
                    }
                ],
            )
            content = response.choices[0].message.content
            if content and content.strip():
                print(f"Provider g4f utilise: {provider_name}")
                return content

        except Exception as e:
            last_error = e
            print(f"Provider {provider_name} en echec: {str(e)}")
            continue

    raise RuntimeError(f"Aucun provider g4f sans cle n'a fonctionne. Derniere erreur: {last_error}")


# Fonction pour afficher le texte extrait d'une image
async def display_text(ctx, text):
    text = (text or "").strip()
    if not text:
        await ctx.send("Aucun texte détecté dans l'image.")
        return

    char_limit = 1900
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + char_limit, len(text))
        if end < len(text):
            last_newline = text.rfind('\n', start, end)
            if last_newline > start:
                end = last_newline + 1
        chunks.append(text[start:end])
        start = end

    for index, chunk in enumerate(chunks, start=1):
        title = "Texte extrait" if len(chunks) == 1 else f"Texte extrait ({index}/{len(chunks)})"
        embed = discord.Embed(title=title, description=chunk, color=0x3498db)
        await ctx.send(embed=embed)


def download_image(
    image_url,
    *,
    timeout=IMAGE_FETCH_TIMEOUT,
    max_bytes=MAX_IMAGE_BYTES,
):
    """Télécharge une image avec timeout et limite de taille."""
    with requests.get(image_url, timeout=timeout, stream=True) as response:
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if not content_type.startswith("image/"):
            raise ValueError("L'URL ne pointe pas vers une image.")

        data = bytearray()
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            data.extend(chunk)
            if len(data) > max_bytes:
                raise ValueError("Image trop volumineuse.")

    if not data:
        raise ValueError("L'image téléchargée est vide.")
    return bytes(data)


def _is_expected_response(message, author, channel):
    """N'accepte que la réponse du même auteur dans le même salon."""
    return message.author == author and message.channel == channel


# Fonction pour améliorer la qualité de l'image
def improve_image_quality(image_url):
    image_bytes = download_image(image_url)
    img = np.array(bytearray(image_bytes), dtype=np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("L'image téléchargée est illisible.")

    # appliquer un filtre pour améliorer la qualité de l'image
    img = cv2.bilateralFilter(img, 9, 75, 75)

    # convertir l'image en format JPG
    ok, jpeg = cv2.imencode('.jpg', img)
    if not ok:
        raise ValueError("Impossible d'encoder l'image en JPEG.")
    return jpeg.tobytes()


# Commande pour extraire et afficher le texte d'une image
@client.command()
async def devoir(ctx):
    try:
        print("Commande devoir appelée")  # Pour le débogage
        await ctx.send("Veuillez envoyer une image ou un lien vers une image valide.")

        message = await client.wait_for(
            'message',
            timeout=60.0,
            check=lambda m: _is_expected_response(m, ctx.author, ctx.channel),
        )

        print("Message reçu")  # Pour le débogage

        if message.attachments:
            attachment = message.attachments[0]
            image_url = attachment.url
            print(f"Image attachée : {image_url}")  # Pour le débogage
        elif message.content:
            image_url = message.content
            print(f"Lien de l'image : {image_url}")  # Pour le débogage
        else:
            print("Aucune image ou lien trouvé")  # Pour le débogage
            return await ctx.send("Veuillez envoyer une image ou un lien vers une image valide.")

        # Améliore la qualité de l'image
        try:
            improved_image_bytes = await asyncio.to_thread(improve_image_quality, image_url)
            print("Image améliorée")  # Pour le débogage
        except Exception as e:
            print(f"Erreur lors de l'amélioration de l'image : {str(e)}")
            return await ctx.send("Une erreur s'est produite lors de l'amélioration de l'image.")

        # Envoie l'image améliorée
        try:
            await ctx.send("Amélioration de l'image ...")
            # Affichage de l'image en cas de besoin
            # await ctx.send(file=discord.File(BytesIO(improved_image_bytes), filename="improve_image.jpg"))
            print("Image envoyée")  # Pour le débogage
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'image : {str(e)}")
            return await ctx.send("Une erreur s'est produite lors de l'envoi de l'image.")

        # Extrait le texte de l'image et l'affiche
        try:
            text = await asyncio.to_thread(extract_text_from_image, improved_image_bytes)
            print(f"Texte extrait : {text}")  # Pour le débogage
            await display_text(ctx, text)
        except Exception as e:
            print(f"Erreur lors de l'extraction du texte : {str(e)}")
            return await ctx.send("Une erreur s'est produite lors de l'extraction du texte.")

        try:
            await ctx.send("Generation de reponses en cours ...")
            markdown_content = await generate_ai_answer(text)
            print(f"Reponse generee : {markdown_content[:100]}")

        except Exception as e:
            print(f"Erreur lors de la génération avec l'IA : {str(e)}")
            return await ctx.send(
                "Erreur IA: aucun provider sans cle n'a repondu. Reessayez dans quelques minutes."
            )

        # Texte formaté pour Discord avec mise en forme
        char_limit = 1900  # Limite de caractères Discord

        # Diviser le texte en morceaux tout en conservant les sauts de ligne et le format
        chunks = []
        start = 0
        while start < len(markdown_content):
            end = start + char_limit
            chunk = markdown_content[start:end]
            if end < len(markdown_content):
                last_newline = chunk.rfind('\n')
                if last_newline != -1:
                    chunk = chunk[:last_newline + 1]
            chunks.append(chunk)
            start += len(chunk)

        # Afficher ou traiter chaque morceau
        for index, chunk in enumerate(chunks, start=1):
            print(f"Bloc {index}:\n{chunk}\n{'-' * 50}")  # Imprime chaque bloc pour vérification
            embed = discord.Embed(description=f"\n{chunk}\n", color=0x00ff00)
            await ctx.send(embed=embed)

    except asyncio.TimeoutError:
        print("Timeout atteint")
        return await ctx.send("Vous n'avez pas envoyé d'image dans le délai imparti.")


def _load_discord_token(path="secrets.json"):
    """Charge le token Discord sans effet de bord à l'import du module."""
    secrets_path = Path(path)
    try:
        with secrets_path.open("r", encoding="utf-8") as file:
            secrets = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier de secrets introuvable: {secrets_path}") from None

    token = secrets.get("discord_bot_token")
    if not token:
        raise ValueError(f"Clé 'discord_bot_token' absente de {secrets_path}")
    return token


# Démarrage du bot avec token
async def start_bot():
    await client.start(_load_discord_token())


async def stop_bot():
    await client.logout()


if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
