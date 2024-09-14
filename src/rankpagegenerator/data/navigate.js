/* jshint esversion: 6 */


function navigate(nav_list) {
    let target = document.getElementById("container");

	const data_container = filter_dict(nav_list);
	const data_columns = get_columns(data_container);

	let options_dict = {};
	for (let col_index in data_columns) {
		let col_name = data_columns[col_index];
		let values = get_values(data_container, col_name);
		values.sort();
        options_dict[ col_name ] = values;
	}
	const table_content = generate_options_table(data_container, options_dict, nav_list);
    target.innerHTML = table_content;
}


function generate_options_table(data_container, options_dict, nav_list) {
	let content = "";
	content += `<div class="bottomspace">navigation: ${nav_list.join(" | ")}</div>`;
	content += `<table class="bottomspace">`;
    for (let option_key in options_dict) {
    	let option_values = options_dict[option_key];
		content += `<tr> <td>${option_key}</td> <td>`;
		let link_list = [];
    	for (let option_index in option_values) {
    		const option_val = option_values[option_index];
    		let next_nav = deep_copy(nav_list);
    		next_nav.push( [option_key, option_val] );
    		const next_string = JSON.stringify(next_nav);
    		let val_label = option_val;
    		if ( val_label === "" ) {
    			val_label = "&lt;empty&gt;";
    		}
    		link_list.push(`<a href='#' onclick='navigate(${next_string})'>${val_label}</a> `);
    	}
		content += link_list.join(" | ");
		content += "</td> </tr>";
    }
    content += "</table>";
    const species = get_values(data_container, ANSWER_COLUMN);
    content += `<div>found species: ${species.join(", ")}</div>`;
    return content;
}


function get_columns( data_container ) {
	let ret_list = [];
	for (let data_index in data_container) {
		let data_row = data_container[data_index];
        for (let row_key in data_row) {
        	if (row_key != ANSWER_COLUMN ) {
	        	ret_list.push(row_key);
        	}
        }	
	}
	return remove_array_dupes(ret_list);
}


// data_container - list of dicts
function get_values( data_container, column_name ) {
	let ret_list = [];
	for (let data_index in data_container) {
		let data_row = data_container[data_index];
        for (let row_key in data_row) {
        	if (row_key == column_name ) {
        		const data_val = data_row[row_key];
	        	ret_list = ret_list.concat( data_val );
        	}
        }	
	}
	return remove_array_dupes(ret_list);
}


function filter_dict( cut_list ) {
	console.log("cutting data: " + to_str(cut_list));
    let curr_data = deep_copy(DATA);
    for (let cut_index in cut_list) {
    	const cut_pair = cut_list[cut_index];
        let cut_key = cut_pair[0];
        let cut_value = cut_pair[1];
	    let new_data = [];
        for (let row_index in curr_data) {
        	let datarow = curr_data[row_index];
            let new_row = filter_row(datarow, cut_key, cut_value);
            if (new_row != undefined) {
                new_data.push(new_row);
            }
        }
        curr_data = new_data;
    }
    console.log("sliced data: " + to_str(curr_data));
    return curr_data;
}


function filter_row( curr_row, cut_key, cut_value ) {
    const value_list = curr_row[cut_key];
    if ( value_list.includes(cut_value) == false ) {
        return undefined;
    }
    let new_row = {};
    for (let curr_key in curr_row) {
        if ( curr_key == cut_key ) {
            continue;
        }
        new_row[curr_key] = curr_row[curr_key];
    }
    return new_row;
}


function deep_copy(data) {
	return JSON.parse(JSON.stringify(data));
}


function to_str(data) {
	return JSON.stringify(data);
}


function remove_array_dupes(data) {
	return [...new Set(data)];
}
