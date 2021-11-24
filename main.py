import jwt # encode/decode token
from transformers import pipeline # for summarization pipline is module of the package transformer
from flask import Flask, request, render_template, redirect, make_response
from flask_sqlalchemy import SQLAlchemy # for working with DB
from coin_scrapper import Scrapper # Our own module that scraps the data from coinmarketcap.com
from threading import Thread # for working with threads, it needs for us to create new thread when we are scrapping data from coinmarketcap.com, otherwise the main thread, website thread will be stopped

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SECRET_KEY'] = "\x15\xc9+pdYY\xad\xeb\xa1%\xdf\xb5\xeb\x80\xc8\xf8fKq\xdc:\xc9" # import os \ os.urandom(24) # "\x15\xc9+pdYY\xad\xeb\xa1%\xdf\xb5\xeb\x80\xc8\xf8fKq\xdc:\xc9"
db = SQLAlchemy(app)
scrapper = Scrapper()
summarization = pipeline("summarization")


class Paragraph(db.Model):
	"""
	Paragraph table in the DB
	"""
	__tablename__ = 'Paragraph'
	id = db.Column('id', db.Integer, primary_key=True)
	title = db.Column('title', db.Text, nullable=False)
	content = db.Column('content', db.Text, nullable=False)
	source = db.Column('source', db.Text, nullable=False)
	published_time = db.Column('published_time', db.Text, nullable=False)
	cryptocurrency = db.Column('cryptocurrency', db.Text, nullable=False)
	url = db.Column('url', db.Text, nullable=False)
	summary = db.Column('summary', db.Text, nullable=False)

	def __init__(self, **fields): # constructor fields is - dictionary
		self.title = fields['title'] # "self" is like as "this" in Java {"title": "SULA"}
		self.content = fields['content'] # fields is dictionary - like as JSON. fields = {"title": "TITLE", "content": 'CONTENT'}
		self.source = fields['source']
		self.published_time = fields['published_time']
		self.cryptocurrency = fields['cryptocurrency']
		self.url = fields['url']

class User(db.Model):
	"""
	User table in the DB
	"""
	__tablename__ = 'User'
	id = db.Column('id', db.Integer, primary_key=True)
	username = db.Column('username', db.Text, nullable=False)
	password = db.Column("password", db.Text, nullable=False)
	is_active = db.Column("is_active", db.Boolean, nullable=False)

@app.route("/registration", methods=["GET", "POST"]) # This router can accept get and post requests/methods
def registration():
	if request.method == "GET": # if a user just come up to the page
		return render_template("registration.html")
	# otherwise
	username = request.form.get('username') # request saves into itself the request data, for example, if in the page there is form, then request will save form data in request.form
	password = request.form.get('password')
	if not username or not password:
		return render_template("registration.html", **{"info": "Type a login and a password both of them"}) # render - fill.
	else:
		user = User()
		user.username = username
		user.password = jwt.encode({"password": password}, app.config["SECRET_KEY"], algorithm="HS256") # encode the password
		user.is_active = True
		db.session.add(user) # Add to db
		db.session.commit() # Save changes

		user_id = jwt.encode({"id": user.id}, app.config["SECRET_KEY"], algorithm="HS256") # encode the user id
		response = make_response(redirect("/")) # make response and save it into "response" variable, response is redirection to main page
		response.set_cookie("user_id", user_id) # set cookie. In the User_id will save Encoded User id. It needs for us to know, where it is placed in the database

		return response

@app.route("/login", methods=["GET", "POST"]) # This router can accept get and post requests/methods
def login():
	if request.method == "GET":
		return render_template("login.html")
	username = request.form.get('username')
	password = request.form.get('password')
	if not username or not password:
		return render_template("login.html", **{"info": "Type a login and a password both of them"})
	else:
		password = jwt.encode({"password": password}, app.config["SECRET_KEY"], algorithm="HS256")
		user = User.query.filter_by(username=username, password=password).first() # get user if exists
		if user: # if user exists
			user.is_active = True
			db.session.commit()

			user_id = jwt.encode({"id": user.id}, app.config["SECRET_KEY"], algorithm="HS256")
			response = make_response(redirect("/"))
			response.set_cookie("user_id", user_id)

			return response
		else:
			return render_template("login.html", **{"info": "Login or password is invalid"})

@app.route("/logout")
def logout():
	user_id = request.cookies.get('user_id')

	if not user_id: # if user even doesn't exist
		return redirect("/")

	usr_id = jwt.decode(user_id, app.config["SECRET_KEY"], algorithms=["HS256"])
	user = User.query.get(usr_id) # Get user from DB where id=usr_id

	if user: # if user exists
		user.is_active = False
		db.session.commit()

		response = make_response(redirect("/login"))
		response.set_cookie("user_id", user_id, max_age=0)

		return response
	else:
		return redirect("/")

@app.route("/", methods=['GET']) # This router can accept only get requests/methods
def coin():
	user_id = request.cookies.get('user_id')

	if not user_id:
		return render_template("main.html", **{"info": "You haven't logged in yet"})

	user_id = jwt.decode(user_id, app.config["SECRET_KEY"], algorithms=["HS256"])
	user = User.query.get(user_id)

	if user:
		if user.is_active:
			coin = request.args.get('coin') #domain/?coin=
			if not coin: # if people didn't input a coin name into input tag in form
				return render_template("main.html", **{"user_logged_in": True})
			else:
				thread = Thread(target=scrapper.get_news_of_cryptocurrency, args=(coin,)) # Create new thread which will scrap data from coinmarketcap.com
				thread.start()

				while thread.is_alive():
					continue # stay here until thread is alive, thread stops when it finish the scrapping. By this line of code, main thread, thread of web site will wait

				if scrapper.last_result == "Error": # in the last_result attribute/property will save the last scrapping data. And if some error is raised by scrapping, this condition is true
					return render_template("main.html", **{"info": "An error has occurred. Try again.", "user_logged_in": True})	
				# otherwise
				for paragraph in scrapper.last_result: # scrapper.last_result = [{"title_of_paragraph": "title", ...}, {"title_of_paragraph": "title", ...}, {"title_of_paragraph": "title", ...}]
					paragraph = Paragraph(**paragraph) # dereferencing the dictionary. **{"title_of_paragraph": "title", ...} = (title_of_paragraph='title', ...)
					paragraph.summary = paragraph.title + paragraph.content
					paragraph.summary = summarization(paragraph.summary, max_length=50)[0]['summary_text'] # It is taken from documentation of transformers package
					db.session.add(paragraph)
					db.session.commit()

				paragraphs = Paragraph.query.all() # get all paragraphs from DB

				return render_template("main.html", **{"paragraphs": paragraphs[len(paragraphs)-5:],
													   "user_logged_in": True})
		else:
			return redirect("/login")
	else:
		return render_template("main.html", **{"info": "You haven't logged in yet"})

@app.route("/shutdown")
def shutdown():
	"""
	it is taken from documentation of the Flask package.
	this function shutdowns the server
	"""
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')
	func()
	return "Good bye"

if __name__ == "__main__":
	# if the code starts in the console
	app.run(debug=True)
