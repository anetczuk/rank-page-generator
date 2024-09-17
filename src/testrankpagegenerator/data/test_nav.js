// 
// Copyright (c) 2024, Arkadiusz Netczuk <dev.arnet@gmail.com>
// All rights reserved.
// 
// This source code is licensed under the BSD 3-Clause license found in the
// LICENSE file in the root directory of this source tree.
// 

/* jshint esversion: 6 */


const mod = require('navigate.js');


function assert_equal(data1, data2) {
    if (!(data1 == data2)) {
        throw new Error("Assertion failed:\n" + " first value: " + data1 + "\nsecond value: " + data2);
    }
}


// ===============================


function test_empty() {
	const values_dict = {};
	let nav = new mod.Navigator(values_dict);

	const response = nav.generate_content();
	assert_equal(response, `<div style="font-weight: bold;">Parametry:</div><table class="bottomspace"></table><div style="font-weight: bold;">Wyniki:</div><div style="margin-left: 4px;"><div></div></div>`);
}


// ===============================


test_empty();
