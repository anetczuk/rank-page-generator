//
// Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
// All rights reserved.
//
// This source code is licensed under the BSD 3-Clause license found in the
// LICENSE file in the root directory of this source tree.
//


/* jshint esversion: 6 */


function start_navigate() {
	const queryString = window.location.search;
	const urlParams = new URLSearchParams(queryString);
	const entries = urlParams.entries();
	let nav_data = {};
	for(const entry of entries) {
		nav_data[ entry[0] ] = entry[1];
	}

    let target = document.getElementById("container");
    let navigator = new Navigator(VALUES_DICT, WEIGHTS_DICT, CATEGORY_PAGE, DETAILS_PAGE, ANSWER_COLUMN, TRANSLATION_DICT);
    target.innerHTML = navigator.generate_content(nav_data);
}


// ==========================================================


class Navigator {
	constructor(values_dict, weights_dict, category_pages, detail_pages, answer_column, translation_dict) {
		this.values_dict = values_dict;
		this.weights_dict = weights_dict;
		this.category_pages = category_pages;
		this.detail_pages = detail_pages;
		this.answer_column = answer_column;
		this.translation_dict = translation_dict;
	}

	generate_content(nav_data = {}) {
		let content = this.generate_filter_table(nav_data);
		content += this.generate_results(nav_data);
		return content;
	}
	
	generate_filter_table(nav_data) {
		let content = "";
		content += `<table cellspacing="0" class="filterstable">`;
		content += `<tr> <th>${this.get_translation("Parameters")}:</th> </tr>`;
	    for (let option_key in this.values_dict) {
	    	if ( option_key == this.answer_column ) {
	    		continue;
	    	}

			let category_content = option_key;
			category_content = this.get_translation(category_content, "category");
			if ( option_key in CATEGORY_PAGE ) {
				const link_href = CATEGORY_PAGE[option_key];
		    	category_content = `<a href="${link_href}">${category_content}</a>`;
			}

	    	const nav_value = nav_data[option_key];
	    	let option_values = this.values_dict[option_key];
			let link_list = [];
	    	for (let option_index in option_values) {
	    		const option_val = option_values[option_index];
	
	    		let next_nav = deep_copy(nav_data);
	    		if ( option_val == nav_value ) {
	    			/// remove
	    			delete next_nav[ option_key ];
	    		} else {
	    			/// add
		    		next_nav[ option_key ] = option_val;
	    		}
	    		
	    		let val_label = option_val;
	    		val_label = this.get_translation(val_label, "category");
	    		if ( val_label === "" ) {
	    			val_label = `[${this.get_translation("empty")}]`;
	    		}
	    		const reqest_url = this.make_request_params(next_nav);
	    		let link_style = "";
	    		if ( nav_value == option_val ) {
	    			link_style = `class="activeoption"`;
	    		}
	    		link_list.push(`<a href='${reqest_url}' ${link_style}>${val_label}</a> `);
	    	}

			let separator = this.get_translation("filterseparator");
			if ( separator === "filterseparator" ) {
				separator = "|";
			}
	    	const links_string = link_list.join(` ${separator} `);
	    	content += `<tr> <td>${category_content}</td> <td>${links_string}</td> </tr>`;
	    }
	    content += "</table>";
	    return content;
	}
	
	/// calculate and present weighted answers
	generate_results(nav_data) {
		let content = "";
		content += `<table cellspacing="0" class="resultstable">`;
		content += `<tr> <th>${this.get_translation("Results")}:</th> </tr>`;
	    if (Object.keys(nav_data).length < 1) {
			content += this.find_simple_answer();
	    } else {
			content += this.find_weighted_answer(nav_data);
		}
		content += "</table>";
// 	    content += `</div>`;
	    return content;
	}

	find_simple_answer() {
	    const answer_list = this.values_dict[this.answer_column];
	    let content = "";
		for (let item_index in answer_list) {
			let item_data = answer_list[item_index];
			let item_content = item_data;
			if ( item_data in DETAILS_PAGE ) {
				const link_href = DETAILS_PAGE[item_data];
		    	item_content = `<a href="${link_href}">${item_content}</a>`;
			}
			let photo_gallery = this.generate_mini_gallery(item_data);
			if ( photo_gallery !== "" ) {
				photo_gallery = `<td>${photo_gallery}</td> `;
			}
			content += `<tr> <td>${item_content}</td> <td></td> ${photo_gallery}</tr>`;
	    }
	    return content;
	}

	find_weighted_answer( nav_data ) {
		const nav_length = Object.keys(nav_data).length;
	    const answer_list = this.values_dict[this.answer_column];
	    let weights_list = [];
		for (let item_index in answer_list) {
			let answer_weight = 0.0;
			const answer_id = answer_list[item_index];
			const answer_weights = WEIGHTS_DICT[answer_id];
		    for (let nav_key in nav_data) {
		    	const nav_value = nav_data[nav_key];
				const weight_val = answer_weights[nav_key][nav_value];
				answer_weight += weight_val;
	        }
	        answer_weight = answer_weight / nav_length * 100.0;
	        weights_list.push([answer_id, answer_weight]);
	    }
	    weights_list.sort(function(item_a, item_b) {
	    	if (item_a[1] < item_b[1]) {
	    		return 1;
	    	}
	    	if (item_a[1] == item_b[1]) {
	    		return item_a[0].localeCompare(item_b[0]);
	    	}
	    	return -1;
	    });
	
	    let content = "";
		for (let item_index in weights_list) {
			const item_data = weights_list[item_index];
			const answer_id = item_data[0];
			const answer_weight = item_data[1];
			const percent_val = Math.round( answer_weight );
			let item_content = answer_id;
			if ( answer_id in DETAILS_PAGE ) {
				const link_href = DETAILS_PAGE[answer_id];
				item_content = `<a href="${link_href}">${answer_id}</a>`;
			}
			let photo_gallery = this.generate_mini_gallery(answer_id);
			if ( photo_gallery !== "" ) {
				photo_gallery = `<td>${photo_gallery}</td> `;
			}
			content += `<tr> <td>${item_content}</td> <td>${percent_val}%</td> ${photo_gallery}</tr>`;
	    }
	    return content;
	}

	generate_mini_gallery(answer_value) {
		if ( answer_value in PHOTOS_DICT === false ) {
			return "";
		}
		const photos_list = PHOTOS_DICT[answer_value];
		let content = "";
		content += "<div class='minigallery'>";
		for (let item_index in photos_list) {
			const item_data = photos_list[item_index];
			content += `<a href="${item_data}"><img src="${item_data}"></a>`;
		}
		content += "</div>";
		return content;
	}

	make_request_params(data_dict) {
		let curr_url = "";
		if (window.location.origin != "null") {
			curr_url += window.location.origin;
		} else {
			curr_url += "file://";
		}
		curr_url += window.location.pathname;
		let url = new URL(curr_url);
		url.search = new URLSearchParams(data_dict);
		return url.toString();
	}

	get_translation(key, group) {
		return get_translation(this.translation_dict, key, group);
	}

}


function get_translation(translation_dict, key, group) {
	if (typeof translation_dict === 'undefined') {
		/// translation dictionary not given
		return key;
	}
	if (typeof group !== 'undefined') {
		const group_dict = translation_dict[group];
		return get_translation(group_dict, key);
	}
	///
	const value = translation_dict[key];
	if (typeof value !== 'undefined') {
		return value;
	}
	/// translation not set for given key
	return key;
}


function deep_copy(data) {
	return JSON.parse(JSON.stringify(data));
}


/// exporting required by unit tests
if (typeof exports !== 'undefined') {
	exports.Navigator = Navigator;
}
