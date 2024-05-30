class VarSetupAutoText{
    // static private method
    static calcEndPos(startPos, deltaPos){
        return {
            'line': startPos.line+deltaPos.line,
            'ch': startPos.ch+deltaPos.ch,
        }
    }
    static calcDeltaPos(text){
        let textArray = text.split('\n');
        let len = textArray.length;
        if (len == 1){
            return {'line':0, 'ch':textArray[0].length};
        }
        else{
            return {'line':len-1, 'ch':textArray[len-1].length};
        }
    }
    static insertSpace(text, spaceNum){
        if (spaceNum == 0) return text;
        let spacesText = Array(spaceNum).fill(' ').join('');
        let textArray = text.split('\n');
        for (let i=1; i<textArray.length; i++){
            textArray[i] = spacesText+textArray[i];
        }
        return textArray.join('\n');
    }
    constructor(cm, startPos, templateText, wrapperClassName, spaceNum = 0, isReadOnly = true, isRecover = true){
        this.cm = cm;
        this.wrapperClassName = wrapperClassName;
        this.lineObject = cm.addLineClass(startPos.line, "wrap", wrapperClassName);
        this.startCh = startPos.ch;
        this.deltaPos = VarSetupAutoText.calcDeltaPos(templateText);
        this.templateText = templateText;
        this.spaceNum = spaceNum;
        this.isReadOnly = isReadOnly;
        this.isRecover = isRecover;
        this.innerText = "";
    }
    resetText(){
        let currentText = this.currentText;
        this.innerText = this.templateText;
        this.currentText = currentText;
    }
    setText(){
        this.innerText = this.currentText;
    }
    checkTemplateText(text){
        return (this.templateText == text);
    }
    get startPos(){
        return {'line': this.lineObject.lineNo(), 'ch':this.startCh};
    }
    set innerText(text){
        this.currentText = text;
        let insertedText = VarSetupAutoText.insertSpace(text, this.spaceNum);
        let newDeltaPos = VarSetupAutoText.calcDeltaPos(insertedText);
        let endPos = VarSetupAutoText.calcEndPos(this.startPos, this.deltaPos);
        this.cm.replaceRange(insertedText, this.startPos, endPos);
        this.deltaPos = newDeltaPos;
        if (this.isReadOnly){
            for (let i=1; i<=this.deltaPos.line; i++){
                this.cm.addLineClass(this.startPos.line+i, "wrap", "cm-readonly");
            }
        }
        else{
            for (let i=0; i<=this.deltaPos.line; i++){
                this.cm.removeLineClass(this.startPos.line+i, "wrap", "cm-readonly");
            }
        }
    }
    removeWrapperClassName(){
        this.cm.removeLineClass(this.lineObject.lineNo(), "wrap", this.wrapperClassName);
    }
}

class AutoTextRule{
    constructor(value){
        this.template = value.template;
        this.isReadOnly = value.isReadOnly;
        this.isRecover = value.isRecover;
    }
    initAutoText(cmObject, lineNum, lineText, anchorName){
        if (lineText.includes(this.template)){
            let space_num = lineText.indexOf(this.template);
            let startPos = {'line': lineNum, 'ch': space_num};
            let varSetupBookMark = new VarSetupAutoText(cmObject, startPos, this.template, anchorName, space_num, this.isReadOnly, this.isRecover);
            return varSetupBookMark;
        }
        return null;
    }
}

class CmElement{
    constructor(value){
        this.cmElement = value.cmElement;
        this.cmOption = value.cmOption;
        this.cmObject = CodeMirror.fromTextArea(
            this.cmElement,
            this.cmOption
        );
        this.autoTexts = [];
        this.autoTextRules = [];
    }
    setCb(eventName, cbFunction){
        this.cmObject.on(eventName, cbFunction);
    }
    setOption(a, b){
        this.cmObject.setOption(a, b);
    }
    addAutoTextRule(value){
        this.autoTextRules.push(value);
    }
    setTemplateText(template, text){
        this.autoTexts.forEach((element)=>{
            if (element.checkTemplateText(template))
                element.innerText = text;
        });
    }
    get autoTextRuleNums(){
        return this.autoTextRules.length;
    }
    showLineClass(){
        let wrapper_elem = this.cmObject.getWrapperElement().getElementsByClassName('CodeMirror-line');
        // unset old read-only config
        for (let i=0; i<wrapper_elem.length; i++){
            let classString = wrapper_elem[i].parentElement.getAttribute("class");
        }
    }
    refresh(){
        this.cmObject.clearHistory();
        this.cmObject.refresh();
    }
    setText(value, refresh_flag = true){
        let wrapper_elem = this.cmObject.getWrapperElement().getElementsByClassName('CodeMirror-line');
        this.autoTexts.forEach(element => {
            element.removeWrapperClassName();
        });
        this.autoTexts = [];
        // unset old read-only config
        for (let i=0; i<wrapper_elem.length; i++){
            this.cmObject.removeLineClass(i, "wrap", "cm-readonly");
        }
        // set new code
        //this.cmObject.getDoc().setValue("");
        this.cmObject.getDoc().setValue(value.content);
        this.cmObject.clearHistory();
        this.cmObject.refresh();
        // set read-only config
        let readOnlyLines = value.readOnlyLines;
        for (let i=0; i<readOnlyLines.length; i++){
            this.cmObject.addLineClass(readOnlyLines[i], "wrap", "cm-readonly");
        }
        
        let count = 0;
        for (let i=0; i<this.cmObject.lineCount(); i++){
            let lineText = this.cmObject.getLine(i);
            let ctx = this;
            this.autoTextRules.forEach( rule => {
                let autoTextObject = rule.initAutoText(ctx.cmObject, i, lineText, 'cm-autotext-'+count);
                if (autoTextObject != null){
                    if (rule.template in value.templates){
                        autoTextObject.innerText = value.templates[rule.template];
                    }
                    else{
                        autoTextObject.innerText = "";
                    }
                    if (autoTextObject.isRecover){
                        ctx.autoTexts.push(autoTextObject);
                    }
                    count++;
                }
            });
        }
        if (refresh_flag){
            this.refresh();
        }
    }
    getText(){
        this.autoTexts.forEach((element)=>{
            element.resetText();
        });
        let code = this.cmObject.getValue();
        let ro_lines = [];
        let wrapper_elem = this.cmObject.getWrapperElement().getElementsByClassName('CodeMirror-line');
        for (let i=0; i<wrapper_elem.length; i++){
            //ro_lines
            let classString = wrapper_elem[i].parentElement.getAttribute("class");
            if(!classString){
                continue;
            }
            let classList = classString.split(" ");
            for (let j=0; j<classList.length; j++){
                if (classList[j] == "cm-readonly"){
                    ro_lines.push(i);
                    break;
                }
            }
        }
        this.autoTexts.forEach((element)=>{
            element.setText();
        });
        return {
            content: code,
            readOnlyLines: ro_lines
        };
    }
}

class FunctionManager{
    constructor(context){
        this.context = context;
        let cmOptions_copied = Object.assign({}, cmOptions);
        cmOptions_copied.scrollbarStyle = 'null';
        this.codeEditors = {
            code: new CmElement({
                cmElement: document.getElementById("code"),
                cmOption: cmOptions
            }),
            vs: new CmElement({
                cmElement: document.getElementById("code-variable-setup"),
                cmOption: cmOptions
            }),
            gvs: new CmElement({
                cmElement: document.getElementById("code-global-variable-setup"),
                cmOption: cmOptions
            }),
            gvsm: new CmElement({
                cmElement: document.getElementById("code-global-variable-setup-main"),
                cmOption: cmOptions
            })
        };
        let ctx = this;
        codeAutoTextRules.forEach(rule => {
            ctx.codeEditors.code.addAutoTextRule(new AutoTextRule(rule));
        });
        
        let read_only_maintain_function = function(cm, change) {
            if(cm.hasFocus() == false){
                return;
            }
            if (ctx.context.gui_enable_flag){
                change.cancel();
            }
            let cm_elem = cm.getWrapperElement().getElementsByClassName('CodeMirror-line');
            let cancel_flag = false;
            for (let line = change.from.line; line<change.to.line; line++){
                if (line >= cm_elem.length){
                    continue ;
                }
                let classString = cm_elem[line].parentElement.getAttribute('class');
                if (classString){
                    let classList = classString.split(" ");
                    for (let i=0; i<classList.length; i++){
                        if (classList[i] == "cm-readonly"){
                            cancel_flag = true;
                            break;
                        }
                    }
                }
            }
            if (cancel_flag){
                change.cancel();
            }
        };
        this.codeEditors.code.setCb('beforeChange', read_only_maintain_function);
        this.codeEditors.gvs.setCb('beforeChange', read_only_maintain_function);
        this.codeEditors.gvsm.setCb('beforeChange', read_only_maintain_function);
        this.codeEditors.vs.setCb('change', function(cm,change) {
            let text = cm.getValue();
            ctx.codeEditors.code.setTemplateText("{*variable_setup*}", text);
        });
        this.codeEditors.gvs.setCb('change', function(cm,change) {
            let gvs_text = ctx.codeEditors.gvs.getText();
            let gvsm_text = ctx.codeEditors.gvsm.getText();
            if (gvs_text.content != gvsm_text.content){
                ctx.codeEditors.gvsm.setText({
                    content: gvs_text.content,
                    readOnlyLines: gvs_text.readOnlyLines,
                    templates: {}
                }, false);
            }
        });
        this.codeEditors.gvsm.setCb('change', function(cm,change) {
            let gvs_text = ctx.codeEditors.gvs.getText();
            let gvsm_text = ctx.codeEditors.gvsm.getText();
            if (gvs_text.content != gvsm_text.content){
                ctx.codeEditors.gvs.setText({
                    content: gvsm_text.content,
                    readOnlyLines: gvsm_text.readOnlyLines,
                    templates: {}
                }, false);
            }
        });
    }
    set_func_code(data, df_name){
        this.codeEditors.code.setText({
            content: data.code,
            readOnlyLines: data.readonly_line,
            templates: {
                "{*df_name*}": df_name.replace(/-/i, '_')
            }
        });
        this.codeEditors.vs.setText({
            content: data.var_setup,
            readOnlyLines: [],
            templates: {}
        });
        this.codeEditors.gvs.refresh();
        return ;
    }
    init(DF, dftype, params, language, func_map, selected_value){
        let mode = "";
        if (language == "Python"){
            mode = "text/x-python";
        }
        else if (language == "C++"){
            mode = "text/x-c++src";
        }
        this.context.fm_state.func_name = "";
        this.context.fm_state.DF = DF;
        this.context.fm_state.DF_name = DF.name;
        this.context.fm_state.dftype = dftype;
        this.context.fm_state.params = params;
        this.context.fm_state.sa_funcs = DF.type_functions;
        this.context.check_lib_function_shown();
        
        this.codeEditors.code.setOption("mode", mode);
        this.codeEditors.vs.setOption("mode", mode);
        this.codeEditors.gvs.setOption("mode", mode);
        this.context.fm_state.sa_func_selected = null;
        this.context.fm_state.show = true;
        setTimeout(() => {
            if (selected_value == -2){
                this.new();
            }
            else{
                this.update_code_content(selected_value, false);
            }
            this.context.check_lib_function_shown();
        }, 100);
        return;
    }
    update_code_content(updateVal, is_lib_func){
        if (updateVal == null) return;
        let func_name = '';
        let ctx = this;
        let style_cb = function(){
            if (is_lib_func){
                ctx.context.fm_state.lib_func_selected = updateVal;
                ctx.context.fm_state.sa_func_selected = null;
                ctx.codeEditors.code.setOption('theme', 'ro');
                ctx.codeEditors.vs.setOption('theme', 'ro');
                ctx.codeEditors.code.setOption('readOnly', 'nocursor');
                ctx.codeEditors.vs.setOption('readOnly', 'nocursor');
            }
            else{
                ctx.context.fm_state.sa_func_selected = updateVal;
                ctx.context.fm_state.lib_func_selected = null;
                ctx.codeEditors.code.setOption('theme', 'func_mgr');
                ctx.codeEditors.vs.setOption('theme', 'func_mgr');
                ctx.codeEditors.code.setOption('readOnly', false);
                ctx.codeEditors.vs.setOption('readOnly', false);
            }
        };

        if (updateVal < 0){
            this.new();
        }
        else if (is_lib_func){
            let lib_object = null;
            let lib_func_object = null;
            this.context.fm_state.lib_funcs.some((element) => {
                let t = element.functions.find(element => element.id == updateVal);
                if (t){
                    lib_object = element;
                    lib_func_object = t;
                    return true;
                }
                return false;
            });
            devicetalk_api(
                "GET",
                "../../../api/function/L/" + updateVal,
                {
                    "dftype" : this.context.fm_state.dftype,
                    "dfparam" : this.context.fm_state.params
                },
                function (data){
                    ctx.set_func_code(data, ctx.context.fm_state.DF_name);
                    ctx.context.fm_state.func_name = lib_func_object.name + "_" + lib_object.name.split('_')[0];
                    ctx.context.fm_state.library_ref = updateVal;
                    ctx.context.fm_state.function_object = null;
                    ctx.context.fm_state.function_df_ref = null;
                    style_cb();
                }
            );
            this.context.fm_state.state_flag = "lib_function";
        }
        else{
            let thisFunction = this.context.fm_state.sa_funcs.find(function(item, index, array){
                return item.id == updateVal;
            });
            let thisFunctionDfRef = this.context.fm_state.DF.function_list.find(function(item, index, array){
                return item.ref.id == updateVal;
            });
            let var_setup = null;
            if (thisFunctionDfRef){
                var_setup = thisFunctionDfRef.var_setup;
            }
            thisFunction.getContent(funcContent => {
                if (var_setup == null){
                    var_setup = funcContent.var_setup;
                }
                this.set_func_code({
                    'code' : funcContent.code,
                    'var_setup' : var_setup,
                    'readonly_line': funcContent.readonly_line
                }, ctx.context.fm_state.DF_name);
                ctx.context.fm_state.func_name = thisFunction.name;
                ctx.context.fm_state.library_ref = thisFunction.library_ref;
                ctx.context.fm_state.function_object = thisFunction;
                ctx.context.fm_state.function_df_ref = thisFunctionDfRef;
                style_cb();
            });
            this.context.fm_state.state_flag = "edit_function";
        }
    }
    new(){
        this.context.fm_state.sa_func_selected = null;
        this.context.fm_state.lib_func_selected = null;
        this.codeEditors.code.setOption('readOnly', false);
        this.codeEditors.vs.setOption('readOnly', false);
        this.codeEditors.code.setOption('theme', 'func_mgr');
        this.codeEditors.vs.setOption('theme', 'func_mgr');
        let ctx = this;
        devicetalk_api(
            "GET",
            "../../../api/function/new/" + `${ctx.context.SA_state.language}/${ctx.context.SA_state.basic_file}`,
            {
                "language" : ctx.context.SA_state.language,
                "dftype" : this.context.fm_state.dftype,
                "dfparam" : this.context.fm_state.params
            },
            function (data){
                ctx.set_func_code(data, ctx.context.fm_state.DF_name);
                ctx.context.fm_state.func_name = '';
                ctx.context.fm_state.library_ref = -1;
                ctx.context.fm_state.function_object = null;
                ctx.context.fm_state.function_df_ref = null;
            }
        );
        this.context.fm_state.state_flag = "new_function";
    }
    save(){
        // Check if function name is empty
        if (this.context.fm_state.func_name == ''){
            alert("Function name can not be empty.");
            return;
        }
        // Find the existed function whose name is same as the string in function-name-entry.
        let same_name_func_object = null;
        // Find in IDF_function_map
        for (let key in this.context.IDF_function_map) {
            let tmp = this.context.IDF_function_map[key].find(func => {
                return func.name == this.context.fm_state.func_name;
            });
            if (tmp != null){
                same_name_func_object = tmp;
                break;
            }
        }
        // Find in ODF_function_map
        for (let key in this.context.ODF_function_map) {
            let tmp = this.context.ODF_function_map[key].find(func => {
                return func.name == this.context.fm_state.func_name;
            });
            if (tmp != null){
                same_name_func_object = tmp;
                break;
            }
        }
        // Alert only if `same_name_func_object` is not null (found)
        // and it is not same as `this.context.fm_state.function_object` (not editing this function)
        if (same_name_func_object != null && same_name_func_object != this.context.fm_state.function_object){
            alert("Function name already existed.");
            return;
        }

        let codeText = this.codeEditors.code.getText();
        let vsText = this.codeEditors.vs.getText();
        let safunc = null;
        // Save as new function
        // When state_flag is `new_function` or user change function's name
        if (this.context.fm_state.state_flag == 'new_function' || this.context.fm_state.func_name != this.context.fm_state.function_object.name){
             safunc = new SaFunction({
                id: -1,
                name: this.context.fm_state.func_name,
                dftype: this.context.fm_state.dftype,
                params: this.context.fm_state.params,
                library_ref: null
            });
            this.context.fm_state.function_object = safunc;
            /*
            addIntoSortedArray(safunc, this.context.fm_state.sa_funcs,
                (a,b) => (a.name > b.name ? 1 : -1));
            */
        }
        else{
            safunc = this.context.fm_state.function_object;
            // Check if the function used by other df
            let usedby_flag = false;
            let df_object_list = (this.context.fm_state.dftype == 'idf') ? this.context.SA_state.IDFs :　this.context.SA_state.ODFs;
            for (const df of df_object_list){
                if (df == this.context.fm_state.DF){
                    continue
                }
                if (df.current == safunc.id){
                    usedby_flag = true;
                    break;
                }
            }
            if (usedby_flag && !safunc.checkedCode(codeText.content)){
                alert("This function used by other DF.\nPlease save as new function if you want to change the code block's content.");
                return;
            }
        }
        let ctx = this;
        // Save function's content.
        safunc.setContent(
            {
                code: codeText.content,
                var_setup: vsText.content,
                readonly_line: codeText.readOnlyLines,
                library_ref: this.context.fm_state.library_ref
            }, 
            func_id => {
                ctx.context.fm_state.sa_func_selected = safunc.id;
                if (!ctx.context.fm_state.DF.hasSaFunction(safunc)){
                    ctx.context.fm_state.DF.addSaFunction(safunc, vsText.content);
                }
                else{
                    ctx.context.fm_state.function_df_ref.var_setup = vsText.content;
                }
                ctx.context.fm_state.DF.setSelected(safunc.id);
                ctx.context.fm_state.state_flag = "edit_function";
                ctx.context.check_lib_function_shown();
                ctx.context.saved_safunction.push(func_id);
            }
        );
        return;
    }
    
    delete(){
        let function_object = this.context.fm_state.function_object;
        let func_id = this.context.fm_state.function_object.id;
        for (let i=0; i<this.context.SA_state.IDFs.length; i++){
            if (this.context.SA_state.IDFs[i] == this.context.fm_state.DF) continue;
            if (this.context.SA_state.IDFs[i].hasSaFunction(function_object)){
                alert("Can't delete.\n This function is already be used.");
                return;
            }
        }
        for (let i=0; i<this.context.SA_state.ODFs.length; i++){
            if (this.context.SA_state.ODFs[i] == this.context.fm_state.DF) continue;
            if (this.context.SA_state.ODFs[i].hasSaFunction(function_object)){
                alert("Can't delete.\n This function is already be used.");
                return;
            }
        }
        if (confirm("Are you sure to delete this SAfunc?")){
            this.context.fm_state.DF.removeSaFunction(function_object);

            this.context.fm_state.sa_func_selected = null;
            this.context.fm_state.lib_func_selected = null;
            this.set_func_code({
                'code' : "",
                'var_setup' : "",
                'readonly_line' : []
            }, this.context.fm_state.DF_name);
            this.new();
            this.context.check_lib_function_shown();
        }
    }
    lib_func_import(){
        this.context.fm_state.sa_func_selected = null;
        this.context.fm_state.lib_func_selected = null;
        this.codeEditors.code.setOption('theme', 'func_mgr');
        this.codeEditors.vs.setOption('theme', 'func_mgr');
        this.codeEditors.code.setOption('readOnly', false);
        this.codeEditors.vs.setOption('readOnly', false);
        this.context.fm_state.state_flag = "new_function";
    }
    set_gvs_code(gvs_object){
        this.codeEditors.gvs.setText({
            content: gvs_object.content,
            readOnlyLines: gvs_object.readonly_lines,
            templates: {}
        });
        this.codeEditors.gvsm.setText({
            content: gvs_object.content,
            readOnlyLines: gvs_object.readonly_lines,
            templates: {}
        });
    }
    get_gvs_code(){
        let result = this.codeEditors.gvs.getText();
        return {
            content: result.content,
            readonly_lines: result.readOnlyLines
        };
    }
}
