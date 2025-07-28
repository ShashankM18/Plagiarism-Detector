# app.py
import os
import difflib
import ast
import itertools
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_ast_nodes(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read())
            return ast.dump(tree)
        except SyntaxError:
            return ""


def compute_similarity(file1_path, file2_path):
    # AST Similarity
    ast1 = get_ast_nodes(file1_path)
    ast2 = get_ast_nodes(file2_path)
    ast_sim = difflib.SequenceMatcher(None, ast1, ast2).ratio()

    # Code-based Similarity
    with open(file1_path, 'r', encoding="utf-8") as f1, open(file2_path, 'r', encoding="utf-8") as f2:
        code1 = f1.read()
        code2 = f2.read()
    diff_sim = difflib.SequenceMatcher(None, code1, code2).ratio()

    final_sim = round(((ast_sim + diff_sim) / 2) * 100, 2)
    return final_sim


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/compare', methods=['POST'])
def compare():
    files = request.files.getlist('files')
    filenames = []

    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        filenames.append(filename)

    file_paths = [os.path.join(app.config['UPLOAD_FOLDER'], name) for name in filenames]
    similarity_results = []

    for file1, file2 in itertools.combinations(zip(filenames, file_paths), 2):
        sim = compute_similarity(file1[1], file2[1])
        similarity_results.append({
            "File 1": file1[0],
            "File 2": file2[0],
            "Similarity (%)": sim
        })

    # Save results to CSV
    df = pd.DataFrame(similarity_results)
    csv_path = os.path.join(RESULT_FOLDER, 'result.csv')
    df.to_csv(csv_path, index=False)

    # Generate Bar Graph
    plt.figure(figsize=(10, 6))
    labels = [f"{r['File 1']} ↔ {r['File 2']}" for r in similarity_results]
    values = [r["Similarity (%)"] for r in similarity_results]
    plt.barh(labels, values, color='skyblue')
    plt.xlabel('Similarity (%)')
    plt.title('Pairwise File Similarity')
    plt.tight_layout()
    graph_path = os.path.join(RESULT_FOLDER, 'graph.png')
    plt.savefig(graph_path)
    plt.close()

    return render_template('results.html', results=similarity_results,
                           graph_image='results/graph.png',
                           csv_download='results/result.csv')


@app.route('/results/<filename>')
def download_file(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.3', port=5006, debug=True)

