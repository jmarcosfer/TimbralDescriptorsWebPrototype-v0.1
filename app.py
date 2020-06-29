from flask import Flask, render_template, request
import freesound
import os, sys
import time
import pandas as pd
import numpy as np

FS_API_KEY=os.getenv('FREESOUND_API_KEY', None)
fs_client = freesound.FreesoundClient()
fs_client.set_token(FS_API_KEY)

# Globals:
metadata_fields = ["id", "name", "duration", "ac_analysis"]
timbral_descriptors = ["ac_brightness", "ac_depth", "ac_hardness", "ac_roughness", "ac_boominess", "ac_warmth", "ac_sharpness"]

##################################################################################
# Helper Functions:
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

	if max_pages <= 1: return page_aggregate
	else:
		for p in range(max_pages-1):
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

def quantize(x):
	if (not np.isnan(x)) and (type(x) is not str):
		return int(round(x))
		
##################################################################################
# START APP:
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/search')
def search():
	total_t = time.perf_counter()
	query_string = request.args.get('q')
	descriptor_filter = request.args.get('f')
	print("Received query")
	# make query & results analysis logic:

	t = time.perf_counter()
	results_pager = query_freesound(query_string, 150, descriptor_filter)
	t_delta = time.perf_counter() - t
	print(f"Received pager in {t_delta} seconds")

	if results_pager.count != 0:
		t = time.perf_counter()
		aggregate_results = scan_pager(results_pager, 1)
		t_delta = time.perf_counter() - t
		print(f"Scanned pager for ({len(aggregate_results)}) results, in {t_delta} seconds")

		t = time.perf_counter()
		aggregate_results_df = pd.DataFrame([ make_pandas_record(s) for s in aggregate_results ])
		t_delta = time.perf_counter() - t
		print("Put results into dataframe in {0} seconds".format(t_delta))

		t = time.perf_counter()
		descriptor_stats = aggregate_results_df.loc[:, timbral_descriptors].describe([0.25, 0.5, 0.75])
		print("Calculated stats...")

		descriptor_dist = {}
		for desc in timbral_descriptors:
			quantized = aggregate_results_df.loc[:, desc].apply(quantize)
			for i in range(101):
				value_select_mask = quantized == i
				descriptor_dist[desc][i] = quantized.loc[value_select_mask].index.tolist() # get IDs with value i for descriptor desc
				
		t_delta = time.perf_counter() - t
		print(f"...and calculated full distributions, all in {t_delta} seconds")
		
		result_ids = [sound.id for sound in aggregate_results[:15]]

		total_delta = time.perf_counter() - total_t
		print(f"Total query time: {total_delta} seconds")
		return render_template('results.html', query_string=query_string, results=result_ids, descriptor_stats=descriptor_stats.to_dict(), format_name=format_name, descriptor_dist=descriptor_dist)
	
	elif results_pager.count == 0:
		return render_template('failure.html', query_string=query_string)