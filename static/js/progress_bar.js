
// Locally Registered Component
var ProgressBar = {
    name: 'ProgressBar',
    props: {
        file: {
            type: File,
        },
        index: {
            type: Number,
            default: -1
        },
        uuid: {
            type: String,
        },
        endpoint_prefix: {
            type: String,
            default: '/devicetalk/api/file'
        }
    },
    data() {
        return {
            state: 0,
            value: 0,
            restartTime: 3,
        }
    },
    mounted (){
        if (this.index == 0){
            this.$parent.upload_start();
        }
    },
    computed: {
        fullWidth () {
            return `width:${this.value}%`;
        },
    },
    methods: {
        start: function(){
            this.state = 1;
            var req = new XMLHttpRequest();
            let ctx = this;
            req.upload.onprogress = function(e){
                if (e.lengthComputable){
                    ctx.value =  Math.floor(100 * e.loaded / e.total);
                }
            }
            req.onreadystatechange = function () {
                if (this.readyState != 4) return;
                if (this.status == 200) {
                    let data = JSON.parse(this.responseText);
                    ctx.state = 2;
                    ctx.$emit('upload_completed', ctx.index);
                }
                else{
                    ctx.state = -1;
                    ctx.restart(this.responseText);
                }
            };
            req.open("POST", this.endpoint_prefix+this.uuid, true);
            req.setRequestHeader('X-CSRFToken', csrftoken);
            req.overrideMimeType('application/octet-stream')
            var fd = new FormData();
            fd.append("file", this.file);
            req.send(fd);
        },
        restart: function(responseText){
            if (this.restartTime > 0){
                this.restartTime--;
                setTimeout(this.start(), 3000);
            }
            else{
                this.$emit('upload_fail', this.index, responseText);
            }
        }
    },
    template: `
        <div class="w3-light-grey w3-round-xlarge">
            <div v-if="state == -1"
                class="w3-red w3-round-xlarge w3-center">
                    Failed
            </div>
            <div v-else-if="state == 2"
                class="w3-blue w3-round-xlarge w3-center">
                    Completed
            </div>
            <div v-else-if="state == 1" 
                class="w3-blue w3-round-xlarge w3-center"
                v-bind:style="fullWidth">
                    {{ value }}%
            </div>
            <div v-else class="w3-round-xlarge w3-center">
                Pending
            </div>
       </div>
    `
};