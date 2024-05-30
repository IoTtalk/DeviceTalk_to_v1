const _file_upload_state = {
    show: false,
    file_upload_id: null,
    files: {}
};

function init(){
    window.ctx_vue = new Vue({
        el: '#app',
        data: { 
            language: _language,
            languages: _languages,
            basic_files_map: {},
            basicfile: 1,
            basicfiles: [],
            files: [],
            file_upload_state: _file_upload_state,
            upload_method: 'PUT',
         },
        components: {
          "progress-bar": ProgressBar
        },
        created: function(){
            this.language_update();
        },
        methods: {
            language_update: function(){
                let ctx = this;
                devicetalk_api(
                    "GET",
                    "language",
                    {},
                    function (data){
                        ctx.languages = data.languages;
                        ctx.basic_files_map = data.basic_files_map;
                        ctx.language_change();
                    }
                );
            },
            language_change: function(){
                this.basicfiles = this.basic_files_map[this.language];
                if (Object.keys(this.basicfiles).length == 0){
                    this.basicfile = -1;
                }
                else{
                    this.basicfile = Object.keys(this.basicfiles)[0];
                }
                this.update_file_list();
            },
            language_add: function(){
                let language_name = "";
                language_name = prompt("Please enter Language name :", "");
                while(this.languages.includes(language_name) || language_name == null || language_name == ""){
                    if (language_name == null){
                        return ;
                    }
                    if (language_name == ""){
                        language_name = prompt("Please enter Language name :", "");
                    }
                    else{
                        language_name = prompt(`"${language_name}" already exist.\nPlease enter Language name :`, "");
                    }
                }
                let ctx = this;
                devicetalk_api(
                    "PUT",
                    "language",
                    {"language": language_name},
                    function (data){
                        ctx.language_update();
                    },
                    function(reason){
                        alert(reason);
                    }
                );
            },
            language_delete: function(){
                if(confirm(`Are you sure to delete language "${this.language}"?`)){
                    let ctx = this;
                    devicetalk_api(
                        "DELETE",
                        "language",
                        {"language": this.language},
                        function (data){
                            ctx.language_update();
                            ctx.language = _language;
                        },
                        function(reason){
                            alert(reason);
                        }
                    );
                }
            },
            handleFiles: function(event, upload_method){
                this.upload_method = upload_method;
                let files = event.target.files;
                let files_dict = {};
                let file_paths = [];
                for (i=0; i<files.length; i++){
                    let rp_array = files[i].webkitRelativePath.split("/").slice(1).join('/');
                    file_paths.push(rp_array);
                    files_dict[rp_array] = {
                        "index" : i,
                        "file" : files[i],
                        "hash" : null
                    };
                }
                if (file_paths.length == 0) return ;
                let ctx = this;
                devicetalk_api(
                    "PUT",
                    "../api/file/",
                    {"files" : file_paths},
                    function (data){
                        if (data.upload_info.length == 0) return;
                        for (const key in data.upload_info) {
                            files_dict[key]["uuid"] = data.upload_info[key];
                        }
                        ctx.file_upload_state.files = files_dict;
                        ctx.file_upload_state.file_upload_id = data.file_upload_id;
                        ctx.file_upload_state.show = true;
                    }
                );
            },
            upload_start: function(){
                this.$refs["file-0"][0].start();
            },
            upload_next: function(file_index){
                let len = Object.keys(this.file_upload_state.files).length
                if (file_index == len-1){
                    this.upload_completed_all();
                }
                else if (file_index < len-1){
                    this.$refs["file-"+(file_index+1).toString()][0].start();
                }
            },
            upload_fail: function(file_index, responseText){
                let ctx = this;
                console.log("Upload fail");
                alert("Upload fail\n"+responseText);
                devicetalk_api(
                    this.upload_method,
                    "file",
                    {
                        "file_upload_id" : this.file_upload_state.file_upload_id,
                        "language": ctx.language,
                        "basicfile_name": "",
                        "state": "failed"
                    },
                    function (data){}
                );
                this.file_upload_state.show = false;
                this.file_upload_state.files = {};
            },
            upload_completed_all: function(){
                let ctx = this;
                console.log("completed all");
                let basicfile_name = "";
                if (this.basicfile == -1 || this.upload_method == "PUT"){
                    let temp_name = prompt("Please enter Language name :", "");
                    while(Object.values(this.basicfiles).includes(temp_name) || temp_name == null || temp_name == ""){
                        if (temp_name == null){
                            this.upload_fail();
                            return ;
                        }
                        if (temp_name == ""){
                            temp_name = prompt("Please enter Basic file name :", "");
                        }
                        else{
                            temp_name = prompt(`"${temp_name}" already exist.\nPlease enter Language name :`, "");
                        }
                    }
                    basicfile_name = temp_name;
                }
                else{
                    basicfile_name = this.basicfiles[this.basicfile];
                }
                devicetalk_api(
                    this.upload_method,
                    "file",
                    {
                        "file_upload_id": this.file_upload_state.file_upload_id,
                        "language": ctx.language,
                        "basicfile_name": basicfile_name,
                        "state": "completed"
                    },
                    function (data){
                        ctx.file_upload_state.show = false;
                        ctx.language_update();
                    },
                    function(reason){
                        alert(reason);
                        ctx.file_upload_state.show = false;
                    }
                );
                this.file_upload_state.files = {};
            },
            update_file_list: function(){
                let ctx = this;
                devicetalk_api(
                    "GET",
                    "file",
                    {
                        "language": ctx.language,
                        "basicfile": ctx.basicfile
                    },
                    function (data){
                        ctx.files = data.files
                        ctx.$forceUpdate();
                    },
                    function(reason){
                        alert(reason);
                    }
                );
            },
            fileDbClick: function(file_uuid){
                window.open('../api/file/'+file_uuid, '_blank');
            },
            update_basicfile: function(){
                if (this.basicfile == -1){
                    alert("Please upload basicfile first.");
                    return;
                }
                document.getElementById('update-file').value = '';
                document.getElementById('update-file').click();
            },
            add_basicfile: function(){
                document.getElementById('add-file').value = '';
                document.getElementById('add-file').click();
            },
            delete_basicfile: function(){
                if(confirm(`Are you sure to delete language "${this.basicfiles[this.basicfile]}"?`)){
                    let ctx = this;
                    devicetalk_api(
                        "DELETE",
                        "file",
                        {
                            "language": ctx.language,
                            "basicfile": ctx.basicfile
                        },
                        function (data){
                            ctx.language_update();
                        },
                        function(reason){
                            alert(reason);
                        }
                    );
                }
            },
            basicfile_change: function(){
                this.update_file_list();
            }
        },
    });
}
