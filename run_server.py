from flask import Flask, request
from controllers.evaluate_github_project import evaluate_github_project

app = Flask(__name__)

@app.route('/evaluate', methods=['POST'])
def evaluate():
    # The evaluate_github_project function expects Flask's request.json
    return evaluate_github_project()

@app.route('/')
def home():
    return "Welcome to the GitHub Project Evaluator API!"

if __name__ == "__main__":
    app.run(debug=True, port=5000)