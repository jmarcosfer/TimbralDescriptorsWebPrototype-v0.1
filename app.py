from flask import Flask, render_template, request
import freesound
import os, sys
import signal
import pandas as pd
import numpy as np

FS_API_KEY=os.getenv('FREESOUND_API_KEY', None)
fs_client = freesound.FreesoundClient()
fs_client.set_token(FS_API_KEY)

# Globals:
metadata_fields = ["id", "name", "tags", "username", "description","duration", "license", "ac_analysis", "previews"]
timbral_descriptors = ["ac_brightness", "ac_depth", "ac_hardness", "ac_roughness", "ac_boominess", "ac_warmth", "ac_sharpness"]

# Helper functions
def query_freesound(query):
	pager = fs_client.text_search(
		query=query,
		fields=",".join(metadata_fields),
		group_by_pack=1,
		page_size=10,
		filter="duration:[* TO 15]"
	)
	return [sound for sound in pager if (sound.ac_analysis and (sound.duration <= 30.0))]

def make_pandas_record(fs_object):
	record = {key: fs_object.as_dict()[key] for key in metadata_fields[:-2] }
	record["path"] = "previews/" + fs_object.previews.preview_lq_mp3.split("/")[-1]
	for descriptor in timbral_descriptors:
		record[descriptor] = fs_object.as_dict()["ac_analysis"][descriptor]
	return record

def get_results(query):
	sounds = query_freesound(query)
	for sound in sounds:
		sound.retrieve_preview("previews/") 
	results_df = pd.DataFrame([ make_pandas_record(s) for s in sounds ])
	return results_df



app = Flask(__name__, static_url_path="/media", static_folder='media')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/search')
def search():
	query_string = request.args.get('q')

	# make query & results analysis logic:
	results = get_results(query_string)
	descriptor_stats = results.loc[:, timbral_descriptors].describe([0.25, 0.5, 0.75])
	# Now, from <results> dataframe, use:
	# - metadata and previews to fill in sample_player_small.html template
	# - descriptor stats to determine slider ranges, steps, and scale warp
	

	return render_template('results.html', query_string=query_string, results=results.loc[:,"name"].tolist())

@app.errorhandler(500)
def shutdown(e, f):
	os.system("rm ./previews/*")
	sys.exit(0)
	print(e)

signal.signal(signal.SIGINT, shutdown)