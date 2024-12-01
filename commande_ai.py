import discord
import asyncio
import json
import traceback
import requests
import io
import cv2
import easyocr
import numpy as np
import time
import pyperclip
import re
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
    try:
        # Télécharge l'image
        response = requests.get(image_url)
        img = Image.open(io.BytesIO(response.content))
        
        # Initialise le lecteur OCR
        reader = easyocr.Reader(['fr'])  # Utilise le français
        
        # Extrait le texte
        result = reader.readtext(np.array(img))
        
        # Rassemble le texte extrait
        extracted_text = ' '.join([item[1] for item in result])
        
        return extracted_text
    
    except Exception as e:
        print(f"Erreur lors de l'extraction du texte : {str(e)}")
        return "Une erreur s'est produite lors de l'extraction du texte."

# Fonction pour afficher le texte extrait d'une image
async def display_text(ctx, text):
    await ctx.send("Le texte extrait de l'image est :")
    await ctx.send(f"```{text}```")


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
        print("Commande devoir appelée")  # Pour le débogage
        await ctx.send("Veuillez envoyer une image ou un lien vers une image valide.")
        
        # Attendre jusqu'à ce qu'un utilisateur envoie un message
        message = await client.wait_for('message', timeout=60.0)
        
        print("Message reçu")  # Pour le débogage
        
        # Vérifie si le message contient une image valide
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
            improved_image_bytes = await improve_image_quality(image_url)
            print("Image améliorée")  # Pour le débogage
        except Exception as e:
            print(f"Erreur lors de l'amélioration de l'image : {str(e)}")
            return await ctx.send("Une erreur s'est produite lors de l'amélioration de l'image.")
        
        # Envoie l'image améliorée
        try:
            await ctx.send(file=discord.File(BytesIO(improved_image_bytes), filename="improve_image.jpg"))
            print("Image envoyée")  # Pour le débogage
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'image : {str(e)}")
            return await ctx.send("Une erreur s'est produite lors de l'envoi de l'image.")
        
        # Extrait le texte de l'image et l'affiche
        try:
            text = extract_text_from_image(image_url)
            print(f"Texte extrait : {text}")  # Pour le débogage
            await display_text(ctx, text)
        except Exception as e:
            print(f"Erreur lors de l'extraction du texte : {str(e)}")
            return await ctx.send("Une erreur s'est produite lors de l'extraction du texte.")
        try:
            #Utilise OpenAI pour générer les réponses de l'exercice
            options = webdriver.ChromeOptions()
            #options.add_argument("--headless")  # Active le mode headless
            options.add_argument("executable_path=chromedriver.exe")
            driver = webdriver.Chrome(options=options)   
            driver.get("https://www.phind.com/")
            driver.set_window_size(1280, 1024)
            # Localise l'élément en utilisant un sélecteur approprié
            message_box = driver.find_element(By.NAME, "q")
            # Cliquez dans l'élément pour activer la zone de texte (si nécessaire)
            message_box.click()
            # Écrire du texte dans l'élément
            message_box.send_keys(f"Répondez aux exercices ou questions qui suivent : {text}")
            # Simuler la touche Entrée pour valider le message
            message_box.send_keys(Keys.ENTER)
            time.sleep(15)
            driver.find_element(By.CSS_SELECTOR, ".fe-copy").click()
            time.sleep(2)
            text_response = pyperclip.paste()
            print(text_response)
        except Exception as e:
            print(f"Erreur lors de la génération avec l'IA : {str(e)}")
            return await ctx.send("Erreur lors de la génération avec l'IA") 
        else :
            # Limite de caractères pour Discord
            char_limit = 1900
            # Diviser le texte en morceaux tout en conservant les sauts de ligne et le format
            chunks = [text_response[i:i + char_limit] for i in range(0, len(text_response), char_limit)]

            # Afficher ou traiter chaque morceau
            for index, chunk in enumerate(chunks, start=1):
                # Trouve l'indice de la ligne "Citations:"
                citations_index = chunk.find('Citations:')
                cleaned_chunk = chunk[:citations_index].strip()
                print(f"Bloc {index}:\n{cleaned_chunk}\n{'-'*50}")
                await ctx.send(f"\n{cleaned_chunk}\n{'-'*50}")
    
           
    except asyncio.TimeoutError:
        print("Timeout atteint")
        return await ctx.send("Vous n'avez pas envoyé d'image dans le délai imparti.")
        

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
