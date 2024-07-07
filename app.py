from flask import Flask, render_template, jsonify, request
from tweevoortwaalf.woordrader import WoordRader
app = Flask(__name__)

@app.route('/')
def index():
    global twaalfletterwoord
    twaalfletterwoord = WoordRader()
    return render_template('index.html', state=twaalfletterwoord.state)

@app.route('/buy_letter', methods=['POST'])
def buy_letter():
    data = request.json
    quizposition = int(data.get('quizposition'))
    twaalfletterwoord.state[quizposition]['bought'] = True
    return jsonify(twaalfletterwoord.state)

@app.route('/guess', methods=['POST'])
def guess():
    data = request.json
    guess = data.get('guess')
    result = "Correct" if guess.lower().replace("ij", "\u0133") == twaalfletterwoord.answer.lower() else "Incorrect"
    result += f"! The correct answer is {twaalfletterwoord.answer.lower()!r}"
    return jsonify({"result": result})

@app.route('/play_again', methods=['POST'])
def play_again():
    global twaalfletterwoord
    twaalfletterwoord = WoordRader()
    return jsonify({"message": "Game reset."})

if __name__ == '__main__':
    app.run(debug=True)
