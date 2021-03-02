from flask import Flask
from flask import request

app = Flask(__name__)
@app.route('/partyrole', methods=['POST'])
def partyRoleListener():
    print(request)
    print(request.json)
    return ''