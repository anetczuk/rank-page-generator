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
	navigate(nav_data);
}


function navigate(nav_data = {}) {
    let target = document.getElementById("container");
	let table_content = generate_options_table(nav_data);
	table_content += generate_results(nav_data);
    target.innerHTML = table_content;
}


function generate_options_table(nav_data) {
	let content = "";
	//content += `<div class="bottomspace">navigation: ${nav_data.join(" | ")}</div>`;
	content += `<table class="bottomspace">`;
    for (let option_key in VALUES_DICT) {
    	if ( option_key == ANSWER_COLUMN ) {
    		continue;
    	}
    	const nav_value = nav_data[option_key];
    	let option_values = VALUES_DICT[option_key];
		content += `<tr> <td>${option_key}</td> <td>`;
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
    		
    		const next_string = JSON.stringify(next_nav);
    		let val_label = option_val;
    		if ( val_label === "" ) {
    			val_label = "&lt;empty&gt;";
    		}
    		const reqest_url = make_request_params(next_nav);
    		let link_style = "";
    		if ( nav_value == option_val ) {
    			link_style = `class="activeoption"`;
    		}
    		link_list.push(`<a href='${reqest_url}' ${link_style}>${val_label}</a> `);
    		//link_list.push(`<a href='#' onclick='navigate(${next_string})'>${val_label}</a> `);
    	}
		content += link_list.join(" | ");
		content += "</td> </tr>";
    }
    content += "</table>";
    return content;
}


/// calculate and present weighted answers
function generate_results(nav_data) {
	let content = "";
    content += `<div style="font-weight: bold;">Found species:</div>`;
    if (Object.keys(nav_data).length < 1) {
		content += find_simple_answer();
    } else {
		content += find_weighted_answer(nav_data);
	}
    return content;
}


function find_simple_answer() {
    const answer_list = VALUES_DICT[ANSWER_COLUMN];
    let content = `<div>`;
	for (let item_index in answer_list) {
		content += `<div>`;
		let item_data = answer_list[item_index];
		if ( item_data in DETAILS_PAGE ) {
			const link_href = DETAILS_PAGE[item_data]
	    	content += `<span><a href="${link_href}">${item_data}</a></span>\n`;
		} else {
		    content += `<span>${item_data}</span>\n`;
		}
		content += `</div>\n`;
    }
    content += `</div>`;
    return content;
}


function find_weighted_answer( nav_data ) {
	const nav_length = Object.keys(nav_data).length;
    const answer_list = VALUES_DICT[ANSWER_COLUMN];
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

    let content = `<div>`;
	for (let item_index in weights_list) {
		const item_data = weights_list[item_index];
		const answer_id = item_data[0];
		const answer_weight = item_data[1];
		const percent_val = Math.round( answer_weight );
	    content += `<div>`;
		if ( answer_id in DETAILS_PAGE ) {
			const link_href = DETAILS_PAGE[answer_id]
	    	content += `<span><a href="${link_href}">${answer_id}</a> (${percent_val}%)</span>\n`;
		} else {
		    content += `<span>${answer_id} (${percent_val}%)</span>\n`;
		}
	    content += `</div>\n`;
    }
    content += `</div>`;
    return content;
}


function make_request_params(data_dict) {
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


function deep_copy(data) {
	return JSON.parse(JSON.stringify(data));
}


function remove_array_dupes(data) {
	return [...new Set(data)];
}
