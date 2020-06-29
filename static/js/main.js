// *************************************************************************** //
// RESULTS CODE:
let resultsDiv = document.getElementById("content_full");
let results = JSON.parse(resultsDiv.dataset.results);
let queryString = resultsDiv.dataset.queryString;

results.forEach((result, index) => {
	resultsDiv.innerHTML += `<div class="sample_player_small">
				<iframe frameborder="0" scrolling="no" src="https://freesound.org/embed/sound/iframe/${result}/simple/medium/" width="481" height="86"></iframe>
			</div>`
})
// *************************************************************************** //


// *************************************************************************** //
// SLIDERS AND CHARTS CODE:
let searchBox = document.getElementById('search-box');
let searchButton = document.getElementById('search_submit');
let searchString = '';
let filterButton = document.getElementById('filter-results');
let sideBar = document.getElementById('sidebar');
let descriptorStats = JSON.parse(sideBar.dataset.stats);
let descriptorDist = JSON.parse(sideBar.dataset.dist);

let sliderDivs = Array.from(document.getElementsByClassName("slider-block"));

let sliders = {};
let histLabels = [...Array(101).keys()]; // range for all AC descriptors 0 - 100

// Utility functions:
function createHistogram(ctx, label, data) {
	let x = [];
	let y = [];
	Object.keys(data).forEach((key) => {
		x.push(data[key].length);
		y.push(key);
	});

	return new Chart(ctx, {
		type: 'bar',
		data: {
			labels: y,
			datasets: [{
				label: label, // from variable
				data: x, // from variable
				borderWidth: 1,
				backgroundColor: 'rgba(0, 0, 0, 0.8)'
			}]
		},
		options: {
			legend: {
				display: false
			},
			scales: {
				yAxes: [{
					display: false
				}]
			}
		}
	});
}

function updateColorBars() {
	// where 'this' refers to the sliderDiv.noUiSlider which fired the event that called this handler
	let sliderRange = this.get();
	
	sliders[this.target.id].chart.data.datasets[0].backgroundColor = function(context) {
		let index = context.dataIndex;
		if (index >= sliderRange[0] && index <= sliderRange[1]) {
			return '#ce1830';
		} else {
			return '#ADADAD';
		}
	};

	sliders[this.target.id].chart.update();
}

function updateDists() {
	const lower = Math.floor(this.get()[0]);
	const size = Math.ceil((this.get()[1] + 1) - lower);
	const otherSliders = [];
	sliderDivs.forEach((div) => {
		if (div.id != this.target.id) {
			otherSliders.push(sliders[div.id]);
		}
	});

	const currentRange = Array.from(new Array(size), (x, i) => i + lower);

	let activeIDs = [];
	currentRange.forEach((value) => {
		sliders[this.target.id].dist[value].forEach((id) => {
			activeIDs.push(id);
		});
	});

	otherSliders.forEach((s) => {
		let x = [];
		Object.keys(s.dist).forEach((v) => {
			let intersection = s.dist[v].filter(id => activeIDs.includes(id));
			x.push(intersection.length);
		});

		s.chart.data.datasets[0].data = x;
		s.chart.update();
	});

}

// Main Loop:
sliderDivs.forEach((sliderDiv, index) => {
	let descriptorName = sliderDiv.id;
	let sliderStats = descriptorStats[descriptorName];
	let cvsCtx = document.querySelector(`.slider-canvas#${ descriptorName }`).getContext('2d');

	sliders[descriptorName] = {
		div: sliderDiv,
		dist: descriptorDist[descriptorName],
		chart: createHistogram(cvsCtx, descriptorName, descriptorDist[descriptorName])
	};

	noUiSlider.create(sliderDiv, {
		start: [sliderStats.min, sliderStats.max],
		connect: true,
		range: {
			'min': 0,
			'max': 100
		}
	});

	// add event handler function:
	
	sliderDiv.noUiSlider.on("update", updateColorBars);
	sliderDiv.noUiSlider.on("change", updateDists);
});

// Run new search when Filter Search Results is clicked:

filterButton.addEventListener('click', function() {
	let searchURL = `${window.location.origin}/search?q=${queryString}&f=`;
	for (let [key, value] of Object.entries(sliders)) {
		let lowerBound = value.div.noUiSlider.get()[0];
		let upperBound = value.div.noUiSlider.get()[1];

		searchURL += `${key}%3A%5B${lowerBound}%20TO%20${upperBound}%5D%20`;
	}
	window.location = searchURL;
});
