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
def format_name(descriptor_name):
	descriptor_name = descriptor_name.replace("ac_", "")
	return descriptor_name.title()

def query_freesound(query, size, descriptor_filter):
	filters = "duration:[* TO 29]"
	if descriptor_filter is not None: filters += descriptor_filter
	pager = fs_client.text_search(
		query=query,
		fields=",".join(metadata_fields),
		group_by_pack=1,
		page_size=size,
		filter=filters
	)

	return pager

def scan_pager(pager, max_pages):
	page_aggregate = [sound for sound in pager if sound.ac_analysis]

	if max_pages >= 1: return page_aggregate
	else:
		for p in range(max_pages):
			try:
				next_page = pager.next_page()
			except ValueError:
				next_page = None
			if next_page is not None:
				page_aggregate += [s for s in next_page if s.ac_analysis]
			elif next_page is None:
				break
		return page_aggregate

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


# start app:
app = Flask(__name__, static_url_path="/media", static_folder='media')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/search')
def search():
	query_string = request.args.get('q')
	descriptor_filter = request.args.get('f')

	print("Received query")
	# make query & results analysis logic:
	results_pager = query_freesound(query_string, 20, descriptor_filter)
	print("Received user results")
	analysis_pager = query_freesound(query_string, 150, descriptor_filter)
	aggregate_results = scan_pager(analysis_pager, 1)
	print(f"Received analysis results ({len(aggregate_results)})")
	aggregate_results_df = pd.DataFrame([ make_pandas_record(s) for s in aggregate_results ])
	print("Put analysis results into dataframe")
	if results_pager.count is not 0:

		descriptor_stats = aggregate_results_df.loc[:, timbral_descriptors].describe([0.25, 0.5, 0.75])
		print("Calculated stats!")
		# Now, from <results> dataframe, use:
		
		# - descriptor stats to determine slider ranges, steps, and scale warp
		
		result_ids = [sound.id for sound in results_pager]

		return render_template('results.html', query_string=query_string, results=result_ids, descriptor_stats=descriptor_stats.to_dict(), format_name=format_name)
	
	elif results_pager.count is 0:
		return render_template('failure.html', query_string=query_string)