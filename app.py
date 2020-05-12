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
metadata_fields = ["id", "name", "tags", "username", "description","duration", "ac_analysis"]
timbral_descriptors = ["ac_brightness", "ac_depth", "ac_hardness", "ac_roughness", "ac_boominess", "ac_warmth", "ac_sharpness"]

# Helper functions
def query_freesound(query):
	pager = fs_client.text_search(
		query=query,
		fields=",".join(metadata_fields),
		group_by_pack=1,
		page_size=20,
		filter="duration:[* TO 29]"
	)
	return [sound for sound in pager if (sound.ac_analysis and (sound.duration <= 30.0))]

def make_pandas_record(fs_object):
	sound_dict = fs_object.as_dict()
	record = {key: sound_dict[key] for key in metadata_fields[:-1] }
	for descriptor in timbral_descriptors:
		try:
			if descriptor in sound_dict["ac_analysis"].keys():
				record[descriptor] = sound_dict["ac_analysis"][descriptor]
		except KeyError as e:
			print(e)
			record[descriptor] = "NaN"
	return record

def get_results(query):
	sounds = query_freesound(query) 
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
	
	# - descriptor stats to determine slider ranges, steps, and scale warp
	
	embed_links = ["https://freesound.org/embed/sound/iframe/{0}/simple/medium/".format(sound_id) for sound_id in results.loc[:,"id"].tolist()]

	return render_template('results.html', query_string=query_string, results=embed_links)
