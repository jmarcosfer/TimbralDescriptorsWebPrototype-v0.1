from flask import Flask, render_template, request
import freesound
import os
import pandas as pd
import numpy as np

# helper functions


app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/search')
def search():
	query_string = request.args.get('q')
	return render_template('results.html', query_string=query_string)