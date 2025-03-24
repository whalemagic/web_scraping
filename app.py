from flask import Flask, render_template, request, jsonify
from database import Database
from config import CATEGORIES

app = Flask(__name__)
db = Database()

@app.route('/')
def index():
    return render_template('index.html', categories=CATEGORIES)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    results = db.search_products(query, category)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True) 