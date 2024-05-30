// Change object to query string
// Ref: https://stackoverflow.com/a/67517152/8224218
function objectToQueryString(queryParameters) {
    serialize = function(params, prefix) {
        return Object.entries(params).reduce((acc, [key, value]) => {
            // remove whitespace from both sides of the key before encoding
            key = encodeURIComponent(key.trim());

            if (params.constructor === Array ) {
              key = `${prefix}`;
            } else if (params.constructor === Object) {
              key = (prefix ? `${prefix}[${key}]` : key);
            }

            /**
             *  - undefined and NaN values will be skipped automatically
             *  - value will be empty string for functions and null
             *  - nested arrays will be flattened
             */
            if (value === null || typeof value === 'function') {
                acc.push(`${key}=`);
            } else if (typeof value === 'object') {
                acc = acc.concat(serialize(value, key));
            } else if(['number', 'boolean', 'string'].includes(typeof value) && value === value) { // self-check to avoid NaN
                acc.push(`${key}=${encodeURIComponent(value)}`);
            }

            return acc;
        }, []);
    }
    return queryParameters ? '?'+serialize(queryParameters).join('&'): '';
}

// Return a XHR object with `application/json` format and `csrf token`
function xhr_setup(methed, path){
    let xhr = new XMLHttpRequest();
    xhr.open(methed, path, true);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8");
    xhr.setRequestHeader('X-CSRFToken', csrftoken);
    return xhr;
}

// A interface calls to create a request to the backend.
function devicetalk_api(method, path, message_object, cb_func, error_cb_func = null){
    if (method == "GET"){
        path = path + objectToQueryString(message_object);
    }
    xhr = xhr_setup(method, path);
    xhr.onreadystatechange = function () {
        if (this.readyState != 4) return;

	console.log(path);
	console.log(this.status);
	    
        if (this.status == 200) {
            let data = JSON.parse(this.responseText);
            cb_func(data.result);
        }
        else if (this.status == 400 ||　this.status == 404) {
            let data = JSON.parse(this.responseText);
            if (error_cb_func){
                error_cb_func(data.reason);
            }
        }
        else if (method == "GET" && this.status == 0){
            alert("Please refresh this page and login again.");
        }
        else if (this.status == 500){
            alert(`Internal Server Error at API\n${method} ${path}.`);
        }
    };
    if (method == "GET"){
        xhr.send();
    }
    else{
        xhr.send(JSON.stringify({
            "data": message_object,
        }));
    }
}

// Start downloading file from url
// Ref: https://stackoverflow.com/questions/3916191/download-data-url-file
function download_zip(path, name){
    let link = document.createElement("a");
    link.download = name;
    link.href = path;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    delete link;
}

// Generate random uuid4
// Ref: https://stackoverflow.com/questions/105034/how-to-create-a-guid-uuid
function uuid4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    });
}

// Insert an element in a sorted array
// https://www.geeksforgeeks.org/what-is-the-efficient-way-to-insert-a-number-into-a-sorted-array-of-numbers-in-javascript/
function addIntoSortedArray(el, arr, cmp) {
    let findLoc = function(el, arr){
        let st = 0;
        let en = arr.length;
        for (let i = 0; i < arr.length; i++) {
            if (cmp(arr[i], el) == 1)
                return i - 1;
        }
        return en;
    }
    arr.splice(findLoc(el, arr) + 1, 0, el);
}
