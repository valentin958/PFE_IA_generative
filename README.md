# PFE_IA_generative
RAG autour d’événements musicaux

# Contexte 

L'intelligence artificielle a transformé de nombreux secteurs, en particulier celui du traitement du langage naturel. Parmi les innovations récentes, les grands modèles de langage (LLM) et les techniques de récupération et génération (RAG) ont prouvé leur capacité à comprendre et générer du texte de manière exceptionnelle. Ces progrès ouvrent la voie à de nouvelles applications, notamment pour la réponse automatique aux questions. Dans le domaine du divertissement, en particulier pour les concerts en France, les utilisateurs recherchent souvent des informations détaillées et personnalisées sur les dates, lieux, prix et genres des spectacles. Cependant, l'obtention de ces informations peut être longue et nécessiter la consultation de multiples sources.

Un système de réponse automatique, capable de traiter des requêtes multicritères, pourrait grandement simplifier ce processus en offrant des réponses précises et personnalisées en temps réel.

# Objectif 

L'objectif principal de ce projet est de développer un système de réponse automatique aux questions sur les concerts en France, en utilisant un **LLM** pour analyser les demandes des utilisateurs et extraire les informations pertinentes d'une base de données d'événements. Ce système devra fournir des réponses détaillées et personnalisées en fonction des critères de recherche de l’utilisateur (comme le lieu, la date, le prix ou le genre musical).  
Le système repose sur une approche hybride appelée **Recherche et Génération Augmentée (RAG)**.  

Plus concrètement, le projet vise à :  
1. Intégrer des techniques de **scraping** pour collecter des informations sur les événements à partir de sites web.  
2. Utiliser **Elasticsearch** pour effectuer des recherches rapides et précises sur ces données.  
3. Appliquer des **modèles de langage** de type **LLM** pour générer des réponses naturelles et cohérentes, adaptées aux critères de l’utilisateur.  
4. Optimiser l'expérience utilisateur en permettant des échanges interactifs et précis, même lorsque les critères de recherche sont flous au début.

# Les étapes

## 1. Collecte et Préparation des Données (Web Scraping)

Le web scraping est utilisé pour collecter des informations sur les événements musicaux. 
Des sites tels que BilletReduc sont choisis pour leur richesse en données, incluant des détails comme le nom des concerts, la date, le lieu, le genre musical et les prix. Les données extraites sont ensuite structurées, nettoyées, et séparées en plusieurs chunk afin d’être indexées dans une base de données Elasticsearch. 
Ce processus de collecte permet de créer une base de données complète et à jour des concerts disponibles, facilitant ainsi la recherche d’événements spécifiques.


```python
import requests
from bs4 import BeautifulSoup

def analyze_page_reduc(url_to_analyze, counter, region_billet):
    try:
        response = requests.get(url_to_analyze)
        document = BeautifulSoup(response.content, 'html.parser')
        
        events = document.select('.bgbeige')
        for event in events:
            head = event.select_one('.head')
            if head:
                artist_name = head.text.split(" dans ")[0].strip()
                show_name = head.text.split(" dans ")[1].strip() if " dans " in head.text else ""
                #artist_page_url = head.find('a')['href']
                artist_page_url = head.get('href')
                show_type = event.select_one('.small').text.split("Spectacles »")[-1].strip()
                description = event.select_one('.libellepreliste').text.strip()
                location_info = event.select_one('.lieu').text.strip()
                dates = event.select_one('.sb').text.strip()
                
                # Further processing (e.g., splitting the location info into parts) goes here
                # Example: location_name, city, postal_code = process_location_info(location_info)
                
                # Extracting additional page info and photo URL
                #description_page, photo_url = analyze_page_reduc_artist(artist_page_url)
                artist_page_url="https://www.billetreduc.com/"+artist_page_url
                print("headlocal",head,"urlocal",artist_page_url)
                '''
                print(f"Artist: {artist_name}, Show: {show_name}, Type: {show_type}")
                print(f"Description: {description}, Dates: {dates}")
                print(f"Location: {location_info}")
                '''
                #print(f"More info: {description_page}, Photo URL: {photo_url}\n")
                
                # Database insertion placeholder
                # insert_into_database(artist_name, show_name, show_type, description, location_info, dates, region_billet, description_page, photo_url)

        # Handling pagination to fetch more events
        # Example: analyze_pagination(document, counter, region_billet)

    except requests.RequestException as e:
        print(f"Request failed: {e}")

def analyze_page_reduc_artist(artist_url):
    try:
        response = requests.get(artist_url)
        document = BeautifulSoup(response.content, 'html.parser')
        
        photo_url = document.select_one('.evtHeader img')['src']
        desc_chapo = document.select_one('[itemprop="description"]').text if document.select_one('[itemprop="description"]') else ""
        desc_resume = document.select_one('#speDescription').text if document.select_one('#speDescription') else ""
        critiques = document.select_one('.FicheBlocCritiques').text if document.select_one('.FicheBlocCritiques') else ""
        
        complete_description = f"{desc_chapo} {desc_resume} {critiques}"
        
        return complete_description, photo_url

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return "", ""

if __name__ == "__main__":
    url_analyzer ="https://www.billetreduc.com/search.htm?jj=&dt=&heure=&prix=0&ages=&salle=&cp=&nbsalle=0&titre=&artistes=&tri=date&type=3&idrub=156&type=3&submit.x=101&submit.y=12" 
    #"https://www.billetreduc.com/search.htm?idrub=3&nbsalle=0&prix=0&tri=date&type=3%2C3&region=J"
    region = "Ile-de-France"  # Example region, you might want to determine this dynamically based on the URL
    analyze_page_reduc(url_analyzer, 0, region)
    '''
    # tout sur un artiste 
    artist_page_url="https://www.billetreduc.com/325461/evt.htm"
    description_page, photo_url = analyze_page_reduc_artist(artist_page_url)
    print(f"More info: {description_page}, Photo URL: {photo_url}\n")
    '''


## Résultat

```


## 2. Utilisation du RAG

Un **RAG** (Retriever-Augmented Generation) combine la récupération d'informations pertinentes (Retriever) et leur utilisation pour générer des réponses cohérentes (Generator). 
Cela permet d'enrichir les modèles de génération de texte en utilisant des données externes pour améliorer la qualité des réponses.

## Le retriever 

Cette phase est cruciale pour extraire les informations pertinentes et fournir du contexte au LLM.

### 1.1 **Extraction des Critères**

- Implémentation d'une fonction qui analyse et identifie les critères principaux dans la question de l'utilisateur. Ces critères peuvent inclure :
    - **Lieu** : ville, quartier ou salle de concert.
    - **Horaire** : date ou période spécifique souhaitée.
    - **Style musical** : genre préféré de l'utilisateur, par exemple, rock, jazz, électro.
    - **Budget** : fourchette de prix ou spécifications de coût.

Cette fonction utilise des méthodes de traitement du langage naturel (NLP) et un LLM pour extraire et normaliser ces critères.

### 1.2 **Requêtage de la Base de Données**

Une fois les critères extraits, on interroge la base de données d'événements musicaux avec trois méthodes complémentaires pour maximiser la pertinence des résultats :

1. **Recherche Booléenne**
    - Requêtes basées sur des opérateurs logiques (AND, OR, NOT) pour un filtrage strict selon les critères de l'utilisateur.
2. **Recherche Vectorielle**
    - Utilisation d'un modèle d'embedding pour trouver des documents pertinents même si les termes exacts ne sont pas présents. Cette méthode compare les représentations vectorielles des critères avec celles des événements.
3. **Reciprocal Rank Fusion (RRF)**
    - Une technique de fusion de résultats qui combine les scores des deux méthodes précédentes pour retourner les documents les plus pertinents. Le RRF favorise les résultats bien classés dans chaque méthode, assurant une meilleure couverture des résultats pertinents.

## Le générateur  

Cette phase transforme les documents obtenus en une réponse naturelle pour l'utilisateur.

### 2.1 **Sélection du LLM**

- Pour garantir des réponses de qualité, une veille régulière est effectuée sur les modèles de langage sur Hugging Face.
- Après évaluation de divers modèles, le choix final se porte sur **Mistral**.

### 2.2 **Prompt Engineering**

Pour structurer la demande au modèle de langage, un *prompt* soigneusement conçu est essentiel. Le *prompt* doit :

- Donner des consignes claires au modèle qui impacteront la façon dont celui-ci répondra.
- Inclure la question initiale de l'utilisateur.
- Fournir le contexte sous forme de documents pertinents extraits de la phase 1.

### Exemple de Template de Prompt

```python
Tu es un organisateur d'évènements expert dans la recommandation de concerts. Tu dois donner des événements répondant à la question de l'utilisateur : {question} en utilisant exclusivement les données pertinentes des documents suivants : {contexte}.
Donne plusieurs propositions, en respectant la hiérarchie des critères : Lieu > Date > Style > Prix.
Les informations doivent inclure : le lieu, la date, le prix, le style musical, et toute autre information pertinente. <>
```

### 2.3 **Génération de la Réponse**

- Le *prompt* est envoyé au modèle, qui génère une réponse en langage naturel.
- La réponse est ensuite formatée pour être conviviale et inclut des recommandations organisées de manière claire :
    - **Proposition 1** : L'événement le plus pertinent selon les critères prioritaires (lieu et date).
    - **Propositions Suivantes** : Options alternatives avec des détails sur le style musical, le prix, etc.
 
# Résultat 

```python
from transformers import AutoTokenizer
from langchain.chains import LLMChain
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
import warnings
import requests
import json
import re

warnings.filterwarnings("ignore")

# Configurations
HUGGINGFACE_REPO_ID = 'mistralai/Mistral-7B-Instruct-v0.3'
HUGGINGFACE_API_TOKEN = 'Mettre votre API TOKEN'

# Initialisation du modèle et du tokenizer
tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_REPO_ID, use_auth_token=HUGGINGFACE_API_TOKEN)
llm = HuggingFaceEndpoint(repo_id=HUGGINGFACE_REPO_ID, huggingfacehub_api_token=HUGGINGFACE_API_TOKEN)

template_criteres = """<<SYS>>
Vous êtes un organisateur d'évènement pour recueillir les critères pertinents tels que le lieu, la date, le prix et le style. Ne donne que la première sortie Json que tu trouves ! Ne continue pas la discussion !
<</SYS>>
History : {history}
IA : {question}
"""
history = ""

template_llm_rag = """<<SYS>>
Vous êtes un organisateur d'évènements expert dans la recommandation de concerts. 
Vous devez repondre à la question de l'utilisateur : {question}
Votre mission est de fournir aux utilisateurs toutes les informations nécessaires pour trouver les concerts idéal en utilisant les documents suivants : {documents}. 
Donne plusieurs (5 max) propositions sachant que le Lieu est le critère principal.
Les informations doivent inclure le lieu, la date, le prix, le style musical, et toute autre information pertinente. 
Assurez-vous d'inclure également une partie du synopsis ou de la description de l'évènement pour donner un aperçu détaillé de chaque concert.
<</SYS>>

"""

prompt_criteres = PromptTemplate(template=template_criteres, input_variables=["question"])

prompt_llm_rag = PromptTemplate(template=template_llm_rag, input_variables=["documents", "question"])

llm_chain = LLMChain(llm=llm, prompt=prompt_criteres, verbose=True)

def extract_criteres(history, question):
    criteres_possibles = ['lieu', 'date', 'prix', 'style']
    prompt = (
        f"Extrait les critères suivants de cette question : '{question}'. "
        f"Retourne uniquement un dictionnaire JSON avec les clés suivantes : {', '.join(criteres_possibles)}. "
        "Inclure des clés supplémentaires si trouvées. "
        "Ne retourne aucun texte supplémentaire. Format de sortie : "
        '{"lieu": "valeur ou null", "date": "valeur ou null", "prix": "valeur ou null", "style": "valeur ou null", "autre": "valeur ou null"}. '
        "Remplace 'valeur' par la valeur réelle du critère trouvé ou 'null' si non spécifié."
    )

    response = llm_chain.invoke({"question": prompt, "history": history})
    response_text = response['text']

    # Ajout de débogage pour vérifier le contenu de response_text
    # print("Response Text:", response_text)

    start_index = response_text.find('{')
 
    # Trouver la position de la dernière accolade fermante
    end_index = response_text.find('}')
 
    # Extraire la sous-chaîne contenant le JSON
    json_string = response_text[start_index:end_index + 1]

    # Suppression des backticks et des espaces inutiles
    cleaned_response_text = json_string.strip().strip("```").strip()
    print(response_text)
  
    critere_dict = json.loads(cleaned_response_text)

    return critere_dict

def search_api(criteres, method, nb_reponses):
    url = "http://azap.sequencia.tv:8004/search_rag"
    query_parts = [f"Spectacle à {criteres.get('lieu')}"]

    if criteres.get('date'):
        query_parts.append(f"{criteres.get('date')}")
    if criteres.get('style'):
        query_parts.append(f"{criteres.get('style')}")
    if criteres.get('prix'):
        query_parts.append(f"{criteres.get('prix')}")
    
    # Ajouter les autres critères dynamiquement
    for key, value in criteres.items():
        if key not in ['lieu', 'date', 'prix', 'style'] and value is not None:
            query_parts.append(f"{value}")

    query = ", ".join(query_parts)
    
    # print(query)

    payload = {
        "query": query,
        "config": {
            "SE_INDEX": "chanson",
            "SE_NUM_RESULTS": nb_reponses,
            "SE_SEARCH_METHODS": method
        }
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    
    results = []
    try:
        for hit in response.json()[query][f'es8_{method}']:
            results.append(hit['_source']['textAll'])
    except KeyError:
        pass
    
    return results

def generate_answer_from_results(criteres):
    # Combine les résultats dans un texte unique
    documents = search_api(criteres, 'rrf', 30)

    llm_chain = LLMChain(llm=llm, prompt=prompt_llm_rag, verbose=True)

    question = [f"Je cherche un concert à {criteres['lieu']} de {criteres['style']}, le {criteres['date']}, avec un budget de {criteres['prix']}."]
    
    for key, value in criteres.items():
        if key not in ['lieu', 'date', 'prix', 'style'] and value is not None:
            question.append(f"{value}")

    question_finale = ", ".join(question)

    # print(question_finale)

    # Génération de la réponse
    response = llm_chain.invoke({
        "question": question_finale,
        "documents": documents
    })
    
    return response['text']

def main():
    history = ""
    # Première interaction
    question = input("Humain : ")
    criteres = extract_criteres(history, question)
    history += f"{criteres}\n"
    # print(criteres)

    for critere, valeur in criteres.items():
        if valeur:
            criteres[critere] = valeur

    for crit in ['lieu','date','prix','style']:
        if not crit in list(criteres.keys()):
            criteres[crit]=None
    
    # Boucle pour compléter les critères manquants
    while True:
        print(criteres)
        api_response = search_api(criteres, 'boolean', 100)
        num_results = len(api_response)
        print(num_results)
        print('recherche terminé')
        # print(history)
        if num_results <= 10 and num_results > 0:
            print(f"{num_results} résultats trouvés :")
            answer = generate_answer_from_results(criteres)
            print(f"IA : {answer}")
            break

        elif num_results == 0 :
            print('Reformule la demande')
            criteres_input = input("Humain : ")
            criteres = extract_criteres(history, criteres_input)
            history += f"Critères : {criteres}\n"

            for critere, valeur in criteres.items():
                if valeur:
                    criteres[critere] = valeur

            for crit in ['lieu','date','prix','style']:
                if not crit in list(criteres.keys()):
                    criteres[crit]=None

        else :
            for critere, valeur in criteres.items():
                if valeur is None:
                    follow_up_prompt = f"Peux-tu donner des details sur le critere de {critere} du concert que tu recherches ?"
             
                    print(f"IA : {follow_up_prompt}")
                    criteres_input = input("Humain : ")
 
                    extracted_criteres = extract_criteres(history, criteres_input)
                    history += f"Critères : {extracted_criteres}\n"
                    # print(extracted_criteres)
                    
                    for critere, valeur in extracted_criteres.items():
                        if valeur:
                            criteres[critere] = valeur
                    for crit in ['lieu','date','prix','style']:
                        if not crit in list(criteres.keys()):
                            criteres[crit]=None
                    break


if __name__ == "__main__":
    main()
```
