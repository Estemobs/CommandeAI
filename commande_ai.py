import discord
import asyncio
import json
import requests
import io
import cv2
import easyocr
import numpy as np
import time
from markdownify import markdownify as md
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver
from seleniumbase import page_actions
from io import BytesIO
from PIL import Image
from discord.ext import commands

intents = discord.Intents.all()
client = commands.Bot(command_prefix=".", intents=intents)

@client.event
async def on_ready():
    print("Le bot est en ligne")
    await client.change_presence(activity=discord.Game(name=".help")) 

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
    await ctx.send("Extraction du texte en cours ...")


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
            await ctx.send("Amélioration de l'image ...")
            # Affichage de l'image en cas de besoin 
            #await ctx.send(file=discord.File(BytesIO(improved_image_bytes), filename="improve_image.jpg"))
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
            await ctx.send("Génération de réponses en cours ...")
            #Utilise OpenAI pour générer les réponses de l'exercice
            driver = Driver(uc=True, headless=True)
            driver.get("https://www.phind.com/")
            print("connexion au site")
            await ctx.send("Connexion au site en cours ...")
            time.sleep(2)
            driver.set_window_size(1280, 1024)
            time.sleep(2)
            # Localise l'élément en utilisant un sélecteur approprié
            message_box = driver.find_element(By.NAME, "q")
            print("Localise l'élément en utilisant un sélecteur approprié")
            await ctx.send("Localisation des éléments ...")
            # Cliquez dans l'élément pour activer la zone de texte (si nécessaire)
            message_box.click()
            time.sleep(2)
            # Écrire du texte dans l'élément
            message_box.send_keys(f"Répondez aux exercices ou questions qui suivent : {text}")
            print("Écrire du texte dans l'élément")
            await ctx.send("Ecriture du texte ...")
            time.sleep(2)
            # Simuler la touche Entrée pour valider le message
            message_box.send_keys(Keys.ENTER)
            print("Simuler la touche Entrée pour valider le message")
            await ctx.send("Simulations des touches ...")
            time.sleep(15)
            # Identifier le texte pertinent
            print("Sélection du prompt")
            await ctx.send("Sélection du prompt ...")
            # Localiser la div contenant l'information par son balisage ou ses classes
            div_element = driver.find_element(By.XPATH, "//div[h6[contains(text(),'Answer | Phind Instant Model')]]")
            html_content = div_element.get_attribute('outerHTML')
            # Convertir le HTML en Markdown
            markdown_content = md(html_content)

        except Exception as e:
            print(f"Erreur lors de la génération avec l'IA : {str(e)}")
            return await ctx.send("Erreur lors de la génération avec l'IA") 
        else :
            if markdown_content.strip().startswith(("###### Answer | Phind Instant Model\n", "Voici ma réponse aux exercices et questions posées :")):
                markdown_content = '\n'.join(line for line in markdown_content.split('\n') if not line.startswith(('######', 'Voici')))
            else:
                pass

           
            char_limit = 1900 

            # Diviser le texte en morceaux tout en conservant les sauts de ligne et le format
            chunks = [markdown_content[i:i + char_limit].rsplit('\n', 1)[0] + '\n' for i in range(0, len(markdown_content), char_limit)]

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
