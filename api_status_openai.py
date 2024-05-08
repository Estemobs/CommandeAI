import openai
openai.api_key = "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"

# Vérifier si l'API répond
try:
    models = openai.Model.list()
    print("L'API répond.")
except Exception as e:
    print("Erreur lors de l'appel de l'API :", e)

# Vérifier si l'API répond
try:
    models = openai.Model.list()
    print("L'API répond.")
except Exception as e:
    print("Erreur lors de l'appel de l'API :", e)

# Poser une question à l'API
question = "Qu'est-ce que l'intelligence artificielle ?"
model_engine = "davinci"  # Choisir le modèle OpenAI à utiliser
response = openai.Completion.create(
    engine=model_engine,
    prompt=question,
    max_tokens=1024,
    n=1,
    stop=None,
    temperature=0.7,
)

# Afficher la réponse
answer = response.choices[0].text.strip()
print("Question :", question)
print("Réponse :", answer)