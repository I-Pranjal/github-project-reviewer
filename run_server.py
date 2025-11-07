from flask import Flask, request
from controllers.evaluate_github_project import evaluate_github_project
import os

app = Flask(__name__)

@app.route('/evaluate', methods=['POST'])
def evaluate():
    # The evaluate_github_project function expects Flask's request.json
    return evaluate_github_project()

@app.route('/')
def home():
    return "Welcome to the GitHub Project Evaluator API!"

if __name__ == "__main__":
    # ✅ Use Render’s assigned port and 0.0.0.0 host
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
