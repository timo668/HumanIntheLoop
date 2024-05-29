from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import json
from openai import OpenAI
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Nodig voor sessies

def Get_samemeaning_info(keyword):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Create completion request
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Geef een korte beschrijving waarom de volgende keywoorden de zelfde betekenis hebben en geef een sugesstie voor de beste. Maximaal 1 zin."},
            {"role": "user", "content": keyword}
        ]
    )
    keyword_message = completion.choices[0].message
    keyword_content = keyword_message.content
    # Extracting words after 'info:'
    reason = keyword_content.split('info:')[0].strip()
    return reason

def Get_clear_info(keyword):
    # return "Dit keyword is onduidelijk omdat het niet duidelijk is waarvoor het staat: een score bij een sportwedstrijd, een politieke overwinning, etc."
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Create completion request
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Geef een korte beschrijving waarom de volgende keywoord onduidelijk is. Maximaal 1 zin."},
            {"role": "user", "content": keyword}
        ]
    )
    keyword_message = completion.choices[0].message
    keyword_content = keyword_message.content
    # Extracting words after 'info:'
    reason = keyword_content.split('info:')[0].strip()
    return reason

@app.route('/clearkeyword')
def clearkeyword():

    # Laad de gegevens uit het JSON-bestand
    with open('data/unclearkeywords.json') as json_file:
        data = json.load(json_file)

    # Haal de huidige index op uit de sessie of begin bij 0
    current_index = session.get('unclear_current_index', 0)
    print(data["unclearKeywords"])

    keyword = data["unclearKeywords"][current_index]

    if data["unclearKeywords"]:
        keyword = data["unclearKeywords"][current_index]
    else:
        keyword = 'default_keyword'

    session['unclearKeywords'] = data["unclearKeywords"]
    # keyword = "1-2-zege"
    keyword_info= Get_clear_info(keyword)
    synonyms = ["a", "b"]
    return render_template('clearkeyword.html', Get_samemeaning_info=keyword_info, Get_Keywords=synonyms, keywords=session['unclearKeywords'], keyword=keyword)

@app.route('/samemeaning')
def index():
    # Laad de gegevens uit het JSON-bestand
    with open('data/Samemeaning.json') as json_file:
        data = json.load(json_file)

    keywords_with_synonyms = [(keyword, synonyms) for keyword, synonyms in data["keywords"].items() if len(synonyms) > 1]

    # Haal de huidige index op uit de sessie of begin bij 0
    current_index = session.get('current_index', 0)

    if keywords_with_synonyms:
        keyword, synonyms = keywords_with_synonyms[current_index]
    else:
        keyword = 'default_keyword'
        synonyms = []

    session['keywords'] = [keyword for keyword, _ in keywords_with_synonyms]  # Bewaar de lijst met sleutelwoorden in de sessie

    delimiter = ", "
    keywords_string = delimiter.join(synonyms)
    keyword_info = Get_samemeaning_info(keywords_string)
    return render_template('samemeaning.html', Get_samemeaning_info=keyword_info, Get_Keywords=synonyms, keywords=session['keywords'])


@app.route('/save_keyword', methods=['POST'])
def save_keyword():
    if request.method == 'POST':
        clicked_keyword = request.json.get('clicked_keyword')
        synonyms = request.json.get('synonyms')

        # Stel de naam van het bestand in waarin de gegevens moeten worden opgeslagen
        filename = 'data/keywordchanges.json'

        # Laad de bestaande gegevens uit het bestand
        try:
            with open(filename, 'r') as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = {}

        if clicked_keyword == "No":
            withoutSipkeyword = synonyms[0].replace("_SKIP_", "")
            existing_data[withoutSipkeyword] = [""]
            next_url = url_for('nextclearkeyword')
            return jsonify({"success": True, "next_url": next_url})
        elif clicked_keyword.startswith("_SKIP_"):
            # Stuur de URL van de volgende route naar de client
            next_url = url_for('nextclearkeyword')
            return jsonify({"success": True, "next_url": next_url})
        else:
            # Voeg de nieuwe gegevens toe aan de bestaande gegevens
            existing_data[clicked_keyword] = synonyms

        # Schrijf de gegevens terug naar het bestand
        with open(filename, 'w') as file:
            json.dump(existing_data, file)

        # Stuur de URL van de volgende route naar de client
        next_url = url_for('next_keyword')

        return jsonify({"success": True, "next_url": next_url})

@app.route('/next')
def next_keyword():
    # Haal de huidige index op uit de sessie of begin bij 0
    current_index = session.get('current_index', 0)

    # Verhoog de index en zorg dat deze binnen de lijst blijft
    if 'keywords' in session:
        current_index = (current_index + 1) % len(session['keywords'])
        session['current_index'] = current_index

    return redirect(url_for('index'))

@app.route('/nextclearkeyword')
def nextclearkeyword():
    # Haal de huidige index op uit de sessie of begin bij 0
    current_index = session.get('unclear_current_index', 0)

    # Verhoog de index en zorg dat deze binnen de lijst blijft
    if 'unclearKeywords' in session:
        current_index = (current_index + 1) % len(session['unclearKeywords'])
        session['unclear_current_index'] = current_index

    return redirect(url_for('clearkeyword'))

if __name__ == '__main__':
    app.run(debug=True)
