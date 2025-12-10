from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test')
def test():
    return jsonify({"status": "ok", "message": "Flask is working"})

if __name__ == '__main__':
    print("Starting Flask on http://0.0.0.0:5000/test")
    app.run(host='0.0.0.0', port=5000, debug=False)
