import discord
import asyncio
import json
import traceback
import aiohttp
import requests
import io
import cv2
import pytesseract
import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from io import BytesIO
from PIL import Image
from discord.ext import commands

intents = discord.Intents.all()
client = commands.Bot(command_prefix=".", intents=intents)

@client.event
async def on_ready():
    print("Le bot est en ligne")
    await client.change_presence(activity=discord.Game(name=".help")) 

#automatisation pour signalé les erreurs
@client.event
async def on_command_error(ctx, error):
    channel = client.get_channel(827566899004440666)
    error_traceback = traceback.format_exception(type(error), error, error.__traceback__)
    error_msg = ''.join(error_traceback)
    await channel.send(f"Erreur lors de l'exécution de la commande {ctx.command} par {ctx.author}: {error}\n```{error_msg}```")
    print(error_msg)
    
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send_help(ctx.command)
        await ctx.send("Erreur de syntaxe : un ou plusieurs arguments manquants")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas le rôle requis pour utiliser cette commande.")


# Fonction pour extraire le texte d'une image
def extract_text_from_image(image_url):
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content))
    text = pytesseract.image_to_string(img, lang='fra')
    return text

# Fonction pour afficher le texte extrait d'une image
async def display_text(ctx, text):
    await ctx.send("Le texte extrait de l'image est :")
    await ctx.send(f"```{text}```")


# Fonction pour vérifier si le message contient une image valide
async def check(ctx):
    if not ctx.message.attachments and not ctx.message.content:
        await ctx.send("Veuillez envoyer une image ou un lien vers une image valide.")
        return False

    # Vérifie si le message contient une pièce jointe valide
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if not attachment.url.lower().endswith(('.png', '.jpeg', '.jpg', '.gif')):
            await ctx.send("Le fichier joint n'est pas une image valide.")
            return False

    # Vérifie si le message contient un lien d'image valide
    if ctx.message.content:
        url = ctx.message.content
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as resp:
                content_type = resp.headers.get('content-type')
                if not content_type or not content_type.startswith('image/'):
                    await ctx.send("Le lien fourni ne pointe pas vers une image valide.")
                    return False

    return True

#fonction pour améliorer la qualité de l'image
async def improve_image_quality(image_url):
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
        await ctx.send("Veuillez envoyer une image ou un lien vers une image valide.")
        message = await client.wait_for('message', check=check, timeout=60.0)

        # Traite la pièce jointe ou le lien d'image valide
        if message.attachments:
            attachment = message.attachments[0]
            image_url = attachment.url
        else:
            image_url = message.content

        # Améliore la qualité de l'image
        improved_image_bytes = await improve_image_quality(image_url)

        # Envoie l'image améliorée
        await ctx.send(file=discord.File(BytesIO(improved_image_bytes), filename="improved_image.jpg"))

        # Extrait le texte de l'image et l'affiche
        text = extract_text_from_image(image_url)
        await display_text(ctx, text)
        
        
        # Utilise OpenAI pour générer les réponses de l'exercice
        options = webdriver.ChromeOptions()
        #options.add_argument("--headless")  # Active le mode headless
        options.add_argument("executable_path=chromedriver.exe")
        driver = webdriver.Chrome(options=options)
        driver.get("https://chatgpt.com/")
        driver.set_window_size(1278, 974)
        element = driver.find_element(By.ID, "prompt-textarea")
        driver.execute_script("if(arguments[0].contentEditable === 'true') {arguments[0].innerText = '<p data-placeholder=\"Message ChatGPT\" class=\"placeholder\"><br class=\"ProseMirror-trailingBreak\"></p>'}", element)
        driver.find_element(By.LINK_TEXT, "Stay logged out").click()
        driver.find_element(By.CSS_SELECTOR, ".placeholder").click()
        element = driver.find_element(By.ID, "prompt-textarea")
        driver.save_screenshot('capture_ecran1.png')
        
        # Après avoir extrait le texte de l'image et avant d'utiliser Selenium
        driver.execute_script(f"if(arguments[0].contentEditable === 'true') {{arguments[0].innerText = '<p>répond a l\'exercice suivant :</p><p>{text}</p>';}}", element)
        element = driver.find_element(By.CSS_SELECTOR, ".icon-md-heavy > path")
        driver.save_screenshot('capture_ecran2.png')
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        element = driver.find_element(By.CSS_SELECTOR, "body")
        driver.save_screenshot('capture_ecran3.png')
        
        # Après avoir exécuté les actions nécessaires pour obtenir la réponse
        response_element = driver.find_element(By.CSS_SELECTOR, ".markdown > p")
        text_response = response_element.text
        driver.save_screenshot('capture_ecran4.png')
        
        
        # Envoie les réponses de l'exercice
        await ctx.send(f"Réponse de ChatGPT : {text_response}")

    except asyncio.TimeoutError:
        await ctx.send("Vous n'avez pas envoyé d'image dans le délai imparti.")
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {str(e)}")

# Lire les secrets à partir du fichier JSON
with open("secrets.json", "r") as file:
    secrets = json.load(file)

# Récupérer les tokens
ddc_token = secrets["ddc_token"]
ddcbeta_token = secrets["ddcbeta_token"]
        
#démarrage du bot avec token 
async def start_bot():
    await client.start(ddcbeta_token)
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
