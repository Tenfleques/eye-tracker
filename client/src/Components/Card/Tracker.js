import React, {Component} from "react";
import Utils from "../../Utilities"
import Select from "../../Controls/Select";

class Tracker extends Component{
    constructor(props){
        super(props);
        this.state = {
            x : props.x || 0,
            y : props.y || 0,
            w : props.w || 10,
            h : props.h || 10,
            fxy :  props.fxy || "default",
            funcs : [],
            prev: null,
            freq : props.freq || 5,
            selectOBJ: null,
        }
        this.onCtrlChange = this.onCtrlChange.bind(this);
    }
    randomUpdate(x, y){
        x = Math.floor(Math.random() * 1000)%this.state.canvas.width
        y = Math.floor(Math.random() * 1000)%this.state.canvas.height;
        return {x, y};
    }
    componentDidMount(){
        const funcs = []
        funcs.push({
            "value" : "default",
            "label" : "default",
            "func" : this.state.fxy
        });
        
        const selectOBJ = {
            "name" : "fxy",
            "caption" : Utils.TextUtils.getLocalCaption("_select_tracker_function"),
            "value" : "default",
            "options" : funcs
        }
        if(funcs.length){
            this.setState({funcs, selectOBJ});
        }
    }
    getFrequency(){
        return this.state.freq;
    }
    onCtrlChange(e){
        const obj = {}
        obj[e.target.id] = e.target.value;
        this.setState(obj);
    }
    update(){
        const date = new Date().getTime();
        let x = this.state.x;
        let y = this.state.y;
        let prev = this.state.prev;
        if(prev.date){
            if (date - prev.date > this.state.freq){
                let func_index = this.state.funcs.findIndex(a => a.value === this.state.fxy);
                let func = this.randomUpdate;
                if(func_index > -1){
                    func = this.state.funcs[func_index].func;
                }
                const res = func(x, y, this.state.w, this.state.h);
                x = res.x;
                y = res.y;
            }
        }else{
            prev = {date,x,y}
        }
        this.setState({prev,x,y});
        return {x, y};
    }
    getSelect(){
        if(this.state.selectOBJ){
            return <Select {...this.state.selectOBJ} onChange={this.onCtrlChange} />
        }
    }
    render(){
        return <>
            {this.getSelect()}
            <div className="form-group">
                <label>
                    {Utils.TextUtils.getLocalCaption("_define_tracker_frequency")}
                </label>   
                <input 
                    type="number" 
                    step="0.01"
                    id="freq"
                    className="form-ctrl"
                    onChange={this.onCtrlChange}
                    value={this.state.freq} />
            </div>
        </>
    }
} 

export default Tracker;