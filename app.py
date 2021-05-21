import random,os
from flask import *
from datetime import datetime
from urllib.parse import urlparse
import sqlite3 as sql #use python 3's built in database so there are less dependencies

# for unique rememberable ids I've implemented
# a filtered version of the 10k most common passwords
# source: https://github.com/danielmiessler/SecLists/blob/master/Passwords/Common-Credentials/10k-most-common.txt
# profanity filter: http://apidemo.pingar.com/Profanity.aspx#wrapper
with open("common_pass.txt") as f:
    wordlist = [line.rstrip() for line in f]

app = Flask(__name__)
app.config["DEBUG"] = 'true'
app.config['STATIC_FOLDER']='static'

def create_db():
    con = sql.connect("urls.db")
    table_def="""
        CREATE TABLE urls (
            id TEXT NOT NULL PRIMARY KEY,
            url TEXT NOT NULL
        );
    """
    with con:
        cur=con.cursor()
        try:
            cur.execute(table_def)
        except Exception as e:
            print(e)
            print("This may indicate you have ran this program before and the table already exists")

def does_table_contain_id(id):
    statement="SELECT COUNT(1) FROM urls WHERE id='%s'"%id
    con = sql.connect("urls.db")
    with con:
        cur=con.cursor()
        return cur.execute(statement).fetchone()[0]
    return False

def get_random_uid():
    # for our random id we will be using the following format
    # The current hour
    # a random word from our password list
    # a random number from 10-99
    # another random word from our password list
    # the current minute
    hour=datetime.now().hour
    word1=random.choice(wordlist)
    number=random.randint(10,99)
    word2=random.choice(wordlist)
    minute=datetime.now().minute
    id = "%s%s%s%s%s"%(hour,word1,number,word2,minute)
    if does_table_contain_id(id):
        return get_random_uid()
    return id

def build_shortened_url(url):
    random_uid=get_random_uid()
    short_url="http://localhost:5000/%s"%random_uid
    statement="INSERT INTO urls(id,url) VALUES(?,?)"
    con = sql.connect("urls.db")
    with con:
        cur=con.cursor()
        cur.execute(statement,(random_uid,url))
    return short_url

def render_landing_page():
    return render_template('index.html')

@app.route("/")
def landing():
    if 'url' in request.args:
        # parameter 'varname' is specified
        url=request.args.get('url')
        if url is None:
            print ("Argument not provided")
        else:
            if urlparse(url).scheme=='':
                url="http://%s"%url
            shortened_url=build_shortened_url(url)
            return render_template('index.html',short_url=shortened_url)
    return render_landing_page()

@app.route('/<short_url>')
def redirect_to_shortened_url(short_url):
    redirection_url="http://localhost:5000"
    statement="SELECT url FROM urls WHERE id='%s'"%short_url
    con = sql.connect("urls.db")
    with con:
        cur=con.cursor()
        res = cur.execute(statement)
        try:
            output=res.fetchone()
            if output is not None:
                redirection_url=output[0]
        except Exception as e:
            print(e)
    return redirect(str(redirection_url),code=301)


if __name__ == '__main__':
    create_db() #create the database if it does not exist already

    # display database contents
    # con = sql.connect("urls.db")
    # with con:
    #     cur=con.cursor()
    #     for x in cur.execute("select * from urls").fetchall():
    #         print(x)


    app.secret_key=os.urandom(12)
    app.run()
