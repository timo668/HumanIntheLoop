from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import json
from openai import OpenAI
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for sessions

def Get_samemeaning_info(keyword):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Create completion request
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Give a brief description of why the following keywords have the same meaning and suggest the best one. Maximum 1 sentence."},
            {"role": "user", "content": keyword}
        ]
    )
    keyword_message = completion.choices[0].message
    keyword_content = keyword_message.content
    # Extracting words after 'info:'
    reason = keyword_content.split('info:')[0].strip()
    return reason

def Get_clear_info(keyword):
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Create completion request
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "Give a brief description of why the following keyword is unclear. Maximum 1 sentence."},
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
    # Load the data from the JSON file
    with open('data/unclearkeywords.json') as json_file:
        data = json.load(json_file)

    # Get the current index from the session or start at 0
    current_index = session.get('unclear_current_index', 0)
    print(data["unclearKeywords"])

    keyword = data["unclearKeywords"][current_index]

    if data["unclearKeywords"]:
        keyword = data["unclearKeywords"][current_index]
    else:
        keyword = 'default_keyword'

    session['unclearKeywords'] = data["unclearKeywords"]
    keyword_info = Get_clear_info(keyword)
    synonyms = ["a", "b"]
    return render_template('clearkeyword.html', Get_samemeaning_info=keyword_info, Get_Keywords=synonyms, keywords=session['unclearKeywords'], keyword=keyword)

@app.route('/samemeaning')
def index():
    # Load the data from the JSON file
    with open('data/Samemeaning.json') as json_file:
        data = json.load(json_file)

    keywords_with_synonyms = [(keyword, synonyms) for keyword, synonyms in data["keywords"].items() if len(synonyms) > 1]

    # Get the current index from the session or start at 0
    current_index = session.get('current_index', 0)

    if keywords_with_synonyms:
        keyword, synonyms = keywords_with_synonyms[current_index]
    else:
        keyword = 'default_keyword'
        synonyms = []

    session['keywords'] = [keyword for keyword, _ in keywords_with_synonyms]  # Save the list of keywords in the session

    delimiter = ", "
    keywords_string = delimiter.join(synonyms)
    keyword_info = Get_samemeaning_info(keywords_string)
    return render_template('samemeaning.html', Get_samemeaning_info=keyword_info, Get_Keywords=synonyms, keywords=session['keywords'])

@app.route('/save_keyword', methods=['POST'])
def save_keyword():
    if request.method == 'POST':
        clicked_keyword = request.json.get('clicked_keyword')
        synonyms = request.json.get('synonyms')

        # Set the filename where the data should be saved
        filename = 'data/keywordchanges.json'

        # Load the existing data from the file
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
            # Send the URL of the next route to the client
            next_url = url_for('nextclearkeyword')
            return jsonify({"success": True, "next_url": next_url})
        else:
            # Add the new data to the existing data
            existing_data[clicked_keyword] = synonyms

        # Write the data back to the file
        with open(filename, 'w') as file:
            json.dump(existing_data, file)

        # Send the URL of the next route to the client
        next_url = url_for('next_keyword')

        return jsonify({"success": True, "next_url": next_url})

@app.route('/next')
def next_keyword():
    # Get the current index from the session or start at 0
    current_index = session.get('current_index', 0)

    # Increment the index and ensure it stays within the list
    if 'keywords' in session:
        current_index = (current_index + 1) % len(session['keywords'])
        session['current_index'] = current_index

    return redirect(url_for('index'))

@app.route('/nextclearkeyword')
def nextclearkeyword():
    # Get the current index from the session or start at 0
    current_index = session.get('unclear_current_index', 0)

    # Increment the index and ensure it stays within the list
    if 'unclearKeywords' in session:
        current_index = (current_index + 1) % len(session['unclearKeywords'])
        session['unclear_current_index'] = current_index

    return redirect(url_for('clearkeyword'))

if __name__ == '__main__':
    app.run(debug=True)
