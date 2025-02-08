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
HUGGINGFACE_API_TOKEN = 'METTRE VOTRE API TOKEN'

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
