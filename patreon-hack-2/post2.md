# Intro

In my [previous post in this series](http://raphael-enochian.tumblr.com/post/133000006820/go-ahead-expose-your-web-debugger-to-the), I gave a rundown on the Patreon hack. I analyzed the attack, security breaches, the source code, and the data dump. In this article, I will reconstruct and demonstrate the exploit itself used by the hackers by attacking  a demo [`Flask`](http://flask.pocoo.org/) server.

> **DISCLAIMER**: *Do not attempt to run this exploit against a server that you don't personally own, or explicitly have permission to do so. I am not liable for any damages or stupidity caused by this demo.*

## Some terms

* **Web framework** - Explaining this is a bit beyond the scope of this article, but an excellent explanation is here: [What is a Web Framework?](http://stackoverflow.com/a/4507543)
* **[`Flask`](http://flask.pocoo.org/)** - A web framework for building web applications with the Python programming language. It's extremely light-weight, small, modular and extensible, and is therefore called a *microframeworks*. Web microframeworks have been gaining a lot of traction in the past few years, over older monolithic frameworks like `Ruby on Rails` and `Django`. Other popular examples of web microframeworks include `Sinatra` (Ruby) and `Node.js` (JavaScript). Flask well established in the web developer community, powering either wholly or partially many popular websites: Pinterest, Twilio, Linked-In, Apple, and Obama's 2012 Election website.
* **[`Werkzeug`](http://werkzeug.pocoo.org/)** - the utility library for Flask that is used (or should be used) only in the development environment. It comes with a powerful in-browser debugger, and has services for hosting a local development web server.

## Setting the Stage

This exploit uses the `Werkzeug` version 0.9.6 -- the same version of Werkzeug running on the Patreon servers (according to the source code dump's `venv` directory). This hack may not work on newer version of `Werkzeug`, which has since been updated with some security changes, like a debugger PIN code ([changelog for Werkzeug 0.11](https://github.com/mitsuhiko/werkzeug/blob/master/CHANGES] ), line 54).

Let's begin by creating a basic Flask app with two endpoints: `index` and `error`.

`my-flask-app.py`

    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        return "Hello, hacker!"

    @app.route('/error')
    def my_error():
        return 3 / 0

    app.run(debug=True, port=7777)

Next, we run the server.

    $ python my-flask-app.py
     * Running on http://127.0.0.1:7777/
     * Restarting with reloader

We now have a fully-fledged Flask application running with a WSGI server.

Open up a web browser and navigate to `http://127.0.0.1:7777`

