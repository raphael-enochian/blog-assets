#!/usr/bin/env python
from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, hacker!"

@app.route('/error')
def my_error():
    return 3 / 0

app.run(debug=True, port=7777)
