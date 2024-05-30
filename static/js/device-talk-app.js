const cmOptions = {
    mode: "python",
    lineNumbers:true,
    theme: "func_mgr",
    tabSize: 4,
    autoRefresh: true,
    indentWithTabs: false,
    indentUnit: 4,
    line: true,
    smartIndent: true,
    styleActiveLine: true,
    extraKeys: {
        // https://github.com/codemirror/CodeMirror/issues/988#issuecomment-549644684
        Tab: (cm) => {
            if (cm.getMode().name === 'null') {
                cm.execCommand('insertTab');
            } else if (cm.somethingSelected()) {
                cm.execCommand('indentMore');
            } else {
                cm.execCommand('insertSoftTab');
            }
        },
        'Shift-Tab': (cm) => cm.execCommand('indentLess'),
    },
};

const codeAutoTextRules = [
    {
        template: "{*variable_setup*}",
        isReadOnly: true,
        isRecover: true
    },
    {
        template: "{*df_name*}",
        isReadOnly: true,
        isRecover: true
    },
    {
        template: "{*new_line*}",
        isReadOnly: false,
        isRecover: false
    }
];

class SaFunction{
    constructor(value){
        this.id = value.id;
        this.name = value.name;
        this.dftype = value.dftype;
        this.params = value.params;
        this.library_ref = value.library_ref;
        this.is_init = false;
    }
    checkedCode(code){
        return (this.code == code);
    }
    setContent(value, cbFunction = null){
        if (!this.checkedCode(value.code) || this.id == -1){
            this.var_setup = value.var_setup;
            this.code = value.code;
            this.readonly_line = value.readonly_line;
            if (value.library_ref > 0){
                this.library_ref = value.library_ref;
            }
            else{
                this.library_ref = null;
            }
            let route = (this.id == -1) ? "PUT" : "../../../api/function/S/"+this.id;
            let ctx = this;
            devicetalk_api(
                (this.id == -1) ? "PUT" : "POST",
                (this.id == -1) ? "../../../api/function/new" : "../../../api/function/S/"+this.id,
                {
                    "func_name" : ctx.name,
                    "dftype": ctx.dftype,
                    "params": ctx.params,
                    "code" : ctx.code,
                    "var_setup" : ctx.var_setup,
                    "readonly_line" : ctx.readonly_line,
                    "library_ref" : ctx.library_ref,
                },
                function (data){
                    ctx.id = data.func_id;
                    ctx.is_init = true;
                    if (cbFunction != null){
                        cbFunction(ctx.id);
                    }
                }
            )
        }
        else{
            if (cbFunction != null){
                cbFunction(this.id);
            }
        }
    }
    getContent(cbFunction){
        if (this.is_init){
            let content = {
                var_setup: this.var_setup,
                code: this.code,
                readonly_line: this.readonly_line
            }
            cbFunction(content);
        }
        else{
            let ctx = this;
            devicetalk_api(
                "GET",
                "../../../api/function/S/"+ctx.id,
                {},
                function (data){
                    ctx.code = data.code;
                    ctx.var_setup = data.var_setup;
                    ctx.readonly_line = data.readonly_line;
                    ctx.library_ref = data.library_ref;
                    let content = {
                        var_setup: data.var_setup,
                        code: data.code,
                        readonly_line: data.readonly_line
                    }
                    ctx.is_init = true;
                    cbFunction(content);
                }
            )
        }
    }
};

class DeviceFeature{
    constructor(value){
        this.name = value.name;
        this.df_type = value.df_type;
        this.params = value.params;
        this.selected = -1;
        this.current = -1;
        this.selected_name = "";
        this.var_setup = "";
        this.function_list = [];
    }
    setTypeFunctionList(value){
        this.type_functions = value;
    }
    setSelected(value){
        if (value == -1){
            this.selected = -1;
            this.current = -1;
            this.selected_name = "";
        }
        else if (value != -2){
            this.selected = -3;
            this.current = value;
            let func_object = this.function_list.find(func => {
                return func.ref.id == value;
            });
            if (func_object == null){
                this.selected = -1;
                this.current = -1;
                this.selected_name = "";
            }
            this.selected_name = func_object.ref.name;
        }
        else{ // value == -2
            if (this.current == -1){
                this.selected = -1;
                this.current = -1;
            }
            else{
                this.selected = -3;
            }
        }
    }
    clearSaFunction(){
        this.function_list.length = 0;
        this.selected = -1;
        this.current = -1;
        this.var_setup = "";
    }
    addSaFunction(saFunction, var_setup = null){
        let cmp = (a,b) => (a.ref.name > b.ref.name ? 1 : -1);
        if (var_setup == null){
            let ctx = this;
            saFunction.getContent(content => {
                let func_ref_object = {
                    var_setup: content.var_setup,
                    ref: saFunction
                };
                addIntoSortedArray(func_ref_object, ctx.function_list, cmp);
            });
        }
        else{
            let func_ref_object = {
                var_setup: var_setup,
                ref: saFunction
            };
            addIntoSortedArray(func_ref_object, this.function_list, cmp);
        }
        let is_func_in_sa_funcs = this.type_functions.some(
            (func, index, array) => {
                return func.id == saFunction.id;
            }
        );
        if (!is_func_in_sa_funcs){
            addIntoSortedArray(saFunction, this.type_functions,
                (a,b) => (a.name > b.name ? 1 : -1));
        }
    }
    removeSaFunction(saFunction){
        for (let i=0; i<this.function_list.length; i++){
            if (this.function_list[i].ref == saFunction){
                if (this.current == saFunction.id){
                    this.selected = -1;
                    this.current = -1;
                    this.var_setup = "";
                }
                this.function_list.splice(i, 1);
                break;
            }
        }
        for (let i=0; this.type_functions.length; i++){
            if (this.type_functions[i] == saFunction){
                this.type_functions.splice(i, 1);
                break;
            }
        }
    }
    hasSaFunction(saFunction){
        for (let i=0; i<this.function_list.length; i++){
            if (this.function_list[i].ref == saFunction) return true;
        }
        return false;
    }
    isSelectedFunction(){
        return this.current > 0;
    }
    toJSON(){
        let functions = [];
        let ctx = this;
        this.function_list.forEach(func_ref => {
            functions.push({
                id: func_ref.ref.id,
                var_setup: func_ref.var_setup,
                selected: ctx.current == func_ref.ref.id
            });
        });
        return {
            name: this.name,
            params: this.params,
            functions: functions
        };
    }
}

function init(){
    let _manual_state = {
        url_map: {},
        src: "",
        show: false,
    };
    
    let _SA_state = {
        device_name: '',
        device_name_list: device_name_list,
        is_new_device: false,
        dm_name: dm_result.dm.name,
        language: languages[0].name,
        languages: [],
        basic_file: languages[0].basic_file[0].id,
        basic_files: languages[0].basic_file,
        basic_file_map: {},
        IDFs: [],
        ODFs: [],
        files: [],
        libraries: []
    };

    languages.forEach(element => {
        _SA_state.languages.push(element.name);
        _SA_state.basic_file_map[element.name] = element.basic_file;
    });
    //_manual_state.src = _SA_state.basic_file_map[languages[0].name][0].url;
    dm_result.idf.forEach(element => {
        if (element.used){
            _SA_state.IDFs.push(new DeviceFeature({
                name: element.name,
                df_type: 'idf',
                params: element.df_type,
            }));
        }
    });
    dm_result.odf.forEach(element => {
        if (element.used){
            _SA_state.ODFs.push(new DeviceFeature({
                name: element.name,
                df_type: 'odf',
                params: element.df_type,
            }));
        }
    });
    
    
    window.ctx_vue = new Vue({
        el: '#all-ctx',
        data: {
            tab_state: "SA",
            DA_state:　DA_state_default,
            SA_state:　_SA_state,
            manual_state: _manual_state,
            fm_state: {
                show: false,
                DF_name: 'None',
                lib_func_selected: null,
                sa_func_selected: null,
                func_name: '',
                sa_funcs: [],
                lib_funcs: [],
                dftype: 'idf',
                params: [],
                state_flag: "init",
                function_df_ref: null,
                function_object: null,
            },
            lib_state: {
                show: false,
                checked: [],
                libs: [],
                selected_lib: null,
                bottom_info_text: "",
            },
            file_upload_state: {
                show: false,
                files: {}
            },
            IDF_function_map: {},
            ODF_function_map: {},
            gui_enable_flag: true,
            saved_safunction: []
         },
        components: {
          "progress-bar": ProgressBar
        },
        created : function(){
            let IDF_function_set = new Set();
            let ODF_function_set = new Set();
            this.SA_state.IDFs.forEach(element => {
                IDF_function_set.add(JSON.stringify(element.params));
            });
            this.SA_state.ODFs.forEach(element => {
                ODF_function_set.add(JSON.stringify(element.params));
            });
            IDF_function_set.forEach(value => {
                this.IDF_function_map[value] = [];
            });
            ODF_function_set.forEach(value => {
                this.ODF_function_map[value] = [];
            });
            this.SA_state.IDFs.forEach(element => {
                element.setTypeFunctionList(this.IDF_function_map[JSON.stringify(element.params)]);
            });
            this.SA_state.ODFs.forEach(element => {
                element.setTypeFunctionList(this.ODF_function_map[JSON.stringify(element.params)]);
            });
            this.SA_state.device_name = '';
            this.update_manual_src();
            this.update_lib_list();
        },
        methods : {
            // Click's callback
            tab_click : function(tab_name){
              this.tab_state = tab_name;
            },
            save_lib_popup_click: function(){
                this.lib_state.bottom_info_text = "";
                this.SA_state.libraries = this.lib_state.checked;
                this.update_function_list();
                this.lib_state.show = false;
            },
            cancel_lib_popup_click: function(){
                this.lib_state.bottom_info_text = "";
                this.lib_state.show = false;
            },
            func_new_click: function(){
                this.fm.new();
            },
            func_save_click: function(){
                this.fm.save();
            },
            func_delete_click: function(){
                this.fm.delete();    
            },
            lib_func_import_click : function(){
                this.fm.lib_func_import();
            },
            upload_api_click : function(){
                document.getElementById('upload-api').click();
            },
            upload_file : function(){
                document.getElementById('upload-file').click();
            },
            download_sa_code_click : function(){
                this.device_save();
            },
            manual_click : function(){
                this.show_manual();
            },
            
            // Device Handle
            update_device_name: function(e){
                let newValue = e.target.value;
                let device_name = "";
                if (newValue == -1) {
                    device_name = prompt("Please enter Device Name :", "");
                    let valid_pattern = /^([A-Z]|[a-z]|_)\w*$/;
                    while(this.SA_state.device_name_list.includes(device_name) || device_name == null || valid_pattern.test(device_name) == false){
                        if (device_name == null){
                            document.getElementById('device-name').value = this.SA_state.device_name;
                            return ;
                        }
                        else if (valid_pattern.test(device_name) == false){
                            device_name = prompt(`INVALID name "${device_name}".\nPlease enter Device Name :`, device_name);
                        }
                        else{
                            device_name = prompt(`"${device_name}" already exist.\nPlease enter Device Name :`, device_name);
                        }
                    }
                    this.SA_state.is_new_device = true;
                    document.getElementById('device-name').value = -2;
                    this.DA_state = DA_state_default;
                    this.DA_state.device_addr = uuid4();
                    this.SA_state.device_name = device_name;
                    this.SA_state.language = languages[0].name;
                    this.language_change();
                    this.gui_enable_flag = false;
                    this.cleanup();
                    return;
                }
                this.SA_state.is_new_device = false;
                device_name = newValue;
                let ctx = this;
                devicetalk_api(
                    "GET",
                    "../../../api/device",
                    {
                        dm_name: dm_result.dm.name,
                        d_name: device_name,
                        username : username
                    },
                    function (data){
                        // Set DA infor.
                        ctx.DA_state = data.device.DA;
                        // Set device name
                        ctx.SA_state.device_name = device_name;
                        // Set language and basic_file
                        ctx.SA_state.language = data.device.SA.basic.language;
                        ctx.SA_state.basic_files = ctx.SA_state.basic_file_map[ctx.SA_state.language];
                        ctx.SA_state.basic_file = data.device.SA.basic.basic_file;
                        // Update manual url
                        ctx.update_manual_src();
                        // Set libs infor.
                        ctx.SA_state.libraries = data.device.SA.libs;
                        ctx.set_df_function_map(data.device.SA.safunction_list);
                        ctx.set_df_sa_function(data.device.SA.safuncs, true);
                        ctx.update_lib_list();
                        ctx.fm.set_gvs_code(data.device.SA.basic.global_var_setup);
                        ctx.set_lib_function(data.libfunction_list);
                        // Enable GUI
                        ctx.gui_enable_flag = false;
                        ctx.cleanup();
                    }
                );
            },
            device_save: function(){
                // Check if all DF have selected sa function.
                let all_selected_flag = true;
                for (let idf of this.SA_state.IDFs){
                    if (!idf.isSelectedFunction()){
                        all_selected_flag = false;
                        break;
                    }
                }
                for (let odf of this.SA_state.ODFs){
                    if (!odf.isSelectedFunction()){
                        all_selected_flag = false;
                        break;
                    }
                }
                if (!all_selected_flag){
                    alert("All DFs must selected a function.");
                    return;
                }
                
                let saved_as_new_flag = true;
                let saved_device_name = this.SA_state.device_name;
                if (!this.SA_state.is_new_device){
                    saved_device_name = prompt(
                        `Save Device\nPlease enter Device Name :\n(Use the same name "${this.SA_state.device_name}" to overwrite the original one)`,
                        this.SA_state.device_name
                    );

                    while(this.SA_state.device_name_list.includes(saved_device_name) || saved_device_name == null || saved_device_name == ""){
                        if (saved_device_name == null){
                            return ;
                        }
                        if (saved_device_name == this.SA_state.device_name){
                            saved_as_new_flag = false;
                            break;
                        }
                        if (saved_device_name == ""){
                            saved_device_name = prompt(
                                `Please enter Device Name :\n(Use the same name "${this.SA_state.device_name}" to overwrite the original one)`, ""
                            );
                        }
                        else{
                            saved_device_name = prompt(
                                `"${saved_device_name}" already exist.\nPlease enter Device Name :
(Use the same name "${this.SA_state.device_name}" to overwrite the original one)`, saved_device_name
                            );
                        }
                    }
                }
                if (saved_as_new_flag){
                    this.DA_state.device_addr = uuid4();
                }
                
                let content_object = {
                    "DA": this.DA_state,
                    "SA": {
                        "basic": {
                            "language": this.SA_state.language,
                            "basic_file": this.SA_state.basic_file,
                            "global_var_setup": this.fm.get_gvs_code()
                        },
                        "safuncs": {
                            "idfs": [],
                            "odfs": []
                        },
                        "libs": this.SA_state.libraries,
                        "safunction_list": []
                    },
                }
                this.SA_state.IDFs.forEach(
                    (element) => {
                        content_object.SA.safuncs.idfs.push(element);
                    }
                );
                this.SA_state.ODFs.forEach(
                    (element) => {
                        content_object.SA.safuncs.odfs.push(element);
                    }
                );
                for (let params in this.IDF_function_map){
                    this.IDF_function_map[params].forEach(safunc => {
                        content_object.SA.safunction_list.push(safunc.id);
                    });
                }
                for (let params in this.ODF_function_map){
                    this.ODF_function_map[params].forEach(safunc => {
                        content_object.SA.safunction_list.push(safunc.id);
                    });
                }
                
                let ctx = this;
                devicetalk_api(
                    "POST",
                    "../../../api/device",
                    {
                        "is_new": saved_as_new_flag,
                        "dm_result": dm_result,
                        "d_name": saved_device_name,
                        "content": content_object,
                        "username" : username
                    },
                    function (data){
                        if (saved_as_new_flag){
                            ctx.SA_state.is_new_device = false;
                            addIntoSortedArray(
                                saved_device_name,
                                ctx.SA_state.device_name_list,
                                (a,b) => (a > b ? 1 : -1)
                            );
                            ctx.$forceUpdate();
                            ctx.SA_state.device_name = saved_device_name;
                            setTimeout(() => {
                                document.getElementById('device-name').value = saved_device_name;
                            }, 500);
                        }
                        ctx.show_manual();
                        download_zip(data.zip_path, data.zip_name);
                    },
                    function(reason){
                        alert(reason);
                    }
                );
            },
            
            // Language
            language_change: function(){
                this.SA_state.basic_files = this.SA_state.basic_file_map[this.SA_state.language];
                this.SA_state.basic_file = this.SA_state.basic_files[0].id;
                this.basic_file_change();
            },
            
            // Basic_file(Platform)
            basic_file_change: function(){
                this.update_lib_list();
                this.SA_state.libraries = [];
                this.update_function_list();
                this.set_df_function_map([]);
                this.set_df_sa_function({idfs: [], odfs: []}, true);
                this.fm.set_gvs_code({
                    content: '',
                    readonly_lines: []
                });
                this.update_manual_src();
            },
            
            // File Handle
            upload_file_onchange : function(event){
                let files = event.target.files;
                let files_dict = {};
                let file_paths = [];
                for (i=0; i<files.length; i++){
                    //let rp_array = files[i].webkitRelativePath.split("/").slice(1).join('/');
                    //file_paths.push(rp_array);
                    let rp_array = files[i].webkitRelativePath;
                    file_paths.push(rp_array);
                    files_dict[rp_array] = {
                        "index" : i,
                        "file" : files[i],
                        "hash" : null
                    };
                }
                document.getElementById('upload-api').value = "";
                if (file_paths.length == 0) return ;
                let ctx = this;
                devicetalk_api(
                    "PUT",
                    "../../../api/file/",
                    {
                        "files": file_paths,
                        "state": "setup"
                    },
                    function (data){
                        for (const key in data.upload_info) {
                            files_dict[key]["uuid"] = data.upload_info[key];
                        }
                        ctx.file_upload_state.files = files_dict;
                        ctx.file_upload_state.file_upload_id = data.file_upload_id;
                        ctx.file_upload_state.show = true;
                    }
                );
            },
            upload_start : function(){
                this.$refs["file-0"][0].start();
            },
            upload_next : function(completed_index){
                let len = Object.keys(this.file_upload_state.files).length;
                if (completed_index == len-1){
                    this.upload_completed_all();
                }
                else if (completed_index < len-1){
                    this.$refs["file-"+(completed_index+1).toString()][0].start();
                }
            },
            upload_fail: function(file_index, responseText){
                alert("Upload fail\n"+responseText);
                let ctx = this;
                devicetalk_api(
                    "PUT",
                    "../../../api/library/"+
                        this.SA_state.language+"/"+
                        this.SA_state.basic_file,
                    {
                        "file_upload_id": this.file_upload_state.file_upload_id,
                        "state": "failed",
                    },
                    function (data){
                        ctx.update_lib_list();
                        ctx.file_upload_state.show = false;
                    }
                );
            },
            upload_completed_all : function(){
                let ctx = this;
                devicetalk_api(
                    "PUT",
                    "../../../api/library/"+
                        this.SA_state.language+"/"+
                        this.SA_state.basic_file,
                    {
                        "file_upload_id": this.file_upload_state.file_upload_id,
                        "state": "completed",
                    },
                    function (data){
                        ctx.update_lib_list();
                        ctx.file_upload_state.show = false;
                    },
                    function(reason){
                        ctx.update_lib_list();
                        alert(reason);
                        ctx.file_upload_state.show = false;
                    }
                );
            },
            
            // Library Handle
            lib_select_click: function(){
                this.lib_state.show = true;
                this.lib_state.checked = this.SA_state.libraries;
                //this.lib_state.selected_lib = null;
            },
            update_lib_list: function(){
                let ctx = this;
                devicetalk_api(
                    "GET",
                    `../../../api/library/${this.SA_state.language}/`+
                        `${this.SA_state.basic_file}`,
                    {username: username},
                    function (data){
                        ctx.lib_state.libs = data.library_list;
                        return;
                    }
                );
            },
            set_lib_function(libfuncs){
                this.fm_state.lib_funcs = libfuncs;
                this.fm_state.lib_funcs.forEach(lib => {
                    lib.functions.forEach(lib_func => {
                        lib_func.isref = false;
                    });
                    lib.hidden = false;
                });
                this.check_lib_function_shown();
            },
            check_lib_function_shown(){
                let check_isref = function(lib_func_id, func_list){
                    let ref_func_object = func_list.find(func => {
                        return func.library_ref == lib_func_id
                    });
                    return ref_func_object != null;
                };
                for(let i = 0; i < this.fm_state.lib_funcs.length; i++){
                    let lib = this.fm_state.lib_funcs[i];
                    let lib_hidden = true;
                    for(let j = 0; j < lib.functions.length; j++){
                        let lib_func = lib.functions[j];
                        let lib_func_isref = false;
                        /*
                        // Check the ref. SA function with all the SA function in this device
                        for (let params in this.IDF_function_map){
                            if (check_isref(lib_func.id, this.IDF_function_map[params])){
                                lib_func_isref = true;
                                break;
                            }
                        }
                        for (let params in this.ODF_function_map){
                            if (lib_func_isref){
                                break;
                            }
                            if (check_isref(lib_func.id, this.ODF_function_map[params])){
                                lib_func_isref = true;
                                break;
                            }
                        }
                        lib_func.isref = lib_func_isref;
                        if (lib_func_isref == false){
                            lib_hidden = false;
                        }
                        ///
                        */
                        /**/
                        // Check the ref. SA function only with the dftype selected
                        if (check_isref(lib_func.id, this.fm_state.sa_funcs)){
                            lib_func.isref = true;
                        }
                        else{
                            lib_func.isref = false;
                            lib_hidden = false;
                        }
                        /**/
                    }
                    lib.hidden = lib_hidden;
                }
            },
            check_lib_dependency: function(index){
                let change_lib_object = this.lib_state.libs[index];
                if (this.lib_state.checked.includes(change_lib_object.id)){
                    let inserted_libs = [];
                    change_lib_object.dependency.forEach(dependency_lib => {
                        if (!this.lib_state.checked.includes(dependency_lib)){
                            this.lib_state.checked.push(dependency_lib);
                            inserted_libs.push(this.get_lib_object_by_id(dependency_lib).name);
                        }
                    });
                    if (inserted_libs.length > 0){
                        this.lib_state.bottom_info_text = "Automatically add dependency library: " + inserted_libs.join(", ");
                    }
                    else{
                        this.lib_state.bottom_info_text = "";
                    }
                }
                else{
                    this.lib_state.bottom_info_text = "";
                }
            },
            get_lib_object_by_id: function(lib_id){
                let lib = this.lib_state.libs.find(lib => {
                    return lib.id == lib_id;
                });
                return lib;
            },
            remove_lib: function(lib_id){
                let index = this.lib_state.checked.indexOf(lib_id);
                if (index !== -1) {
                  this.lib_state.checked.splice(index, 1);
                }
                this.lib_state.bottom_info_text = "";
            },
            get_sorted_checked_libs: function(){
                let checked_libs = [];
                this.lib_state.checked.forEach(lib_id => {
                    checked_libs.push(this.get_lib_object_by_id(lib_id));
                });
                checked_libs.sort((a, b) => (a.name > b.name ? 1 : -1));
                return checked_libs;
            },
            
            // Function Handle
            update_function_list(){
                let ctx = this;
                devicetalk_api(
                    "GET",
                    "../../../api/function",
                    {
                        libs: this.SA_state.libraries
                    },
                    function (data){
                        ctx.set_df_function_map(data.safunction_list);
                        ctx.set_df_sa_function(data.df_safuncs);
                        ctx.set_lib_function(data.libfunction_list);
                        ctx.fm.set_gvs_code(data.global_var_setup);
                    }
                );
            },
            func_select_change: function(event, DF, dftype, params){
                let selected_value = event.target.value;
                DF.setSelected(selected_value);
                if (dftype == "idf"){
                    this.fm.init(
                        DF, dftype, params,
                        this.SA_state.language,
                        this.IDF_function_map,
                        selected_value
                    );
                }
                else{
                    this.fm.init(
                        DF, dftype, params,
                        this.SA_state.language,
                        this.ODF_function_map,
                        selected_value
                    );
                }
                return ;
            },
            sa_function_change: function(){
                this.fm.update_code_content(this.fm_state.sa_func_selected, false);
            },
            lib_function_change: function(){
                this.fm.update_code_content(this.fm_state.lib_func_selected, true);
            },
            set_df_sa_function(safuncs, is_set_selected = false){
                let func = function(safunc_info, df_list, df_function_map){
                    let df_name = safunc_info.name;
                    let params = JSON.stringify(safunc_info.params);
                    let df_object = df_list.find(df => {
                        return df.name == df_name;
                    });
                    if (df_object != null){
                        let selected_value = -1;
                        safunc_info.functions.forEach(df_func => {
                            let func_object = df_function_map[params].find(map_func => {
                                return map_func.id == df_func.id;
                            });
                            if (func_object != null){
                                df_object.addSaFunction(func_object, df_func.var_setup);
                                if (df_func.selected){
                                    selected_value = df_func.id;
                                }
                            }
                        });
                        if (is_set_selected){
                            df_object.setSelected(selected_value);
                        }
                        else{
                            df_object.setSelected(-1);
                        }
                    }
                };
                this.SA_state.IDFs.forEach(df => {
                    df.clearSaFunction();
                });
                this.SA_state.ODFs.forEach(df => {
                    df.clearSaFunction();
                });
                safuncs.idfs.forEach(element => {
                    func(element, this.SA_state.IDFs, this.IDF_function_map);
                });
                safuncs.odfs.forEach(element => {
                    func(element, this.SA_state.ODFs, this.ODF_function_map);
                });
            },
            set_df_function_map(sa_function){
                for (let key in this.IDF_function_map){
                    this.IDF_function_map[key].length = 0;
                }
                for (let key in this.ODF_function_map){
                    this.ODF_function_map[key].length = 0;
                }
                sa_function.forEach( func => {
                    let params = JSON.stringify(func.params);
                    if (func.dftype == "idf"){
                        if (!(params in this.IDF_function_map)){
                            this.IDF_function_map[params] = [];
                        }
                        this.IDF_function_map[params].push(new SaFunction(func));
                    }
                    else{
                        if (!(params in this.ODF_function_map)){
                            this.ODF_function_map[params] = [];
                        }
                        this.ODF_function_map[params].push(new SaFunction(func));
                    }
                });
                for (let params in this.IDF_function_map){
                    this.IDF_function_map[params].sort((a,b) => (a.name > b.name ? 1 : -1));
                }
                for (let params in this.ODF_function_map){
                    this.ODF_function_map[params].sort((a,b) => (a.name > b.name ? 1 : -1));
                }
            },
            
             // Manual
            show_manual: function(){
                this.manual_state.show = true;
            },
            update_manual_src: function(){
                let basic_file_object = this.SA_state.basic_files.find(x => x.id === this.SA_state.basic_file);
                this.manual_state.src = basic_file_object.url;
            },

            // Cleanup
            cleanup: function(){
                let ctx = this;
                devicetalk_api(
                    "PATCH",
                    "",
                    {
                        "saved_safunction": this.saved_safunction
                    },
                    function (data){
                        ctx.saved_safunction = [];
                    }
                );
            },
            
            // Global variable setup main
            check_gvsm_shown: function(){
                // If other popup is shown, set gvsm to hidden to avoid scroll bar
                // show at the top.
                if (this.lib_state.show || this.fm_state.show || this.manual_state.show){
                    return false;
                }
                if (this.fm){
                    setTimeout(() => {this.fm.codeEditors.gvsm.cmObject.refresh();}, 50);
                }
                return true;
            }
        },
    });

    // Bind a FunctionManager to `ctx_vue.fm` after ctx_vue load.
    window.ctx_vue.fm = new FunctionManager(window.ctx_vue);
    // Add beforeunload listener
    window.addEventListener(
        "beforeunload", 
        function(event){
            // Send cleanup beforeunload
            window.ctx_vue.cleanup();
        }, false
    );
}
