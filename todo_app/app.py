from flask import Flask, render_template, request, jsonify
import json
import os

import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TODO_FILE = os.path.join(BASE_DIR, 'todos.json')

def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_todos(todos):
    with open(TODO_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/todos', methods=['GET'])
def get_todos():
    todos = load_todos()
    return jsonify(todos)

@app.route('/api/todos', methods=['POST'])
def add_todo():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': '文字不能為空'}), 400
    
    todos = load_todos()
    todos.append(text)
    save_todos(todos)
    return jsonify({'success': True, 'todos': todos})

if __name__ == '__main__':
    app.run(debug=True)