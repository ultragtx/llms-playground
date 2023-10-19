from flask import Flask, render_template, request
import markdown
import os
import json
import logging
import argparse
import mistune

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Directory containing JSON files
JSON_DIR = '../output'

def get_all_json_files(base_dir):
    """Recursively get all JSON files in a directory and its sub-directories."""
    json_files = []
    for dirpath, dirnames, filenames in os.walk(base_dir):
        for filename in [f for f in filenames if f.endswith('.json')]:
            rel_dir = os.path.relpath(dirpath, base_dir)
            rel_file = os.path.join(rel_dir, filename)
            json_files.append(rel_file)
    return json_files

@app.template_filter()
def markdown_filter(text):
    return mistune.markdown(text)

@app.route('/', methods=['GET', 'POST'])
def index():
    print('index')
    json_files = get_all_json_files(JSON_DIR)

    print(json_files)
    
    content = None
    if request.method == 'POST':
        selected_file = request.form.get('file_selector')
        with open(os.path.join(JSON_DIR, selected_file), 'r') as file:
            content = json.load(file)

    return render_template('index.html', json_files=json_files, content=content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Web app for llms-evaluation.")

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=18000,
        help="Port",
    )

    args = parser.parse_args()
    app.run(debug=True, port=args.port)
