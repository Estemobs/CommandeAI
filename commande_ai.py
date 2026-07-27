import discord
import asyncio
import json
import requests
import io
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

_EASYOCR_READER = None

intents = discord.Intents.all()
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
    await ctx.send("Extraction du texte en cours ...")

# Fonction pour améliorer la qualité de l'image
def improve_image_quality(image_url):
    response = requests.get(image_url)
    img = np.array(bytearray(response.content), dtype=np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    # appliquer un filtre pour améliorer la qualité de l'image
    img = cv2.bilateralFilter(img, 9, 75, 75)

    # convertir l'image en format JPG
    ret, jpeg = cv2.imencode('.jpg', img)
    img_bytes = jpeg.tobytes()
    return img_bytes


# Commande pour extraire et afficher le texte d'une image
@client.command()
async def devoir(ctx):
    try:
        print("Commande devoir appelée")  # Pour le débogage
        await ctx.send("Veuillez envoyer une image ou un lien vers une image valide.")

        message = await client.wait_for('message', timeout=60.0)

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
        try:
            loop = asyncio.get_event_loop()
            improved_image_bytes = await loop.run_in_executor(None, improve_image_quality, image_url)
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
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, extract_text_from_image, improved_image_bytes)
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
            print(f"Bloc {index}:\n{chunk}\n{'-'*50}")  # Imprime chaque bloc pour vérification
            embed = discord.Embed(description=f"\n{chunk}\n", color=0x00ff00)
            await ctx.send(embed=embed)

    except asyncio.TimeoutError:
        print("Timeout atteint")
        return await ctx.send("Vous n'avez pas envoyé d'image dans le délai imparti.")

# Lire les secrets à partir du fichier JSON
with open("secrets.json", "r") as file:
    secrets = json.load(file)

# Récupérer les tokens
discord_bot_token = secrets["discord_bot_token"]

# Démarrage du bot avec token
async def start_bot():
    await client.start(discord_bot_token)

async def stop_bot():
    await client.logout()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        loop.run_until_complete(stop_bot())
    finally:
        loop.close()
