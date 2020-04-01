import React, { Component } from 'react';

class AutoCompleteTextBox extends Component {
    constructor(props) {
        super(props);
        this.state = {
            options : props.options,
            filtered_options : []
        }
        this.autoComplete = this.autoComplete.bind(this);
        this.handleClickOutside = this.handleClickOutside.bind(this);
    }
    componentDidUpdate(old_props, old_state){   
        if(old_props.options.length !== this.props.options.length){
            if(this.props.filtered_options.length){
                this.setState({options : this.props.options, filtered_options : this.props.options})
            }else{
                this.setState({options : this.props.options})
            }
        }
    }
    componentDidMount() {
        document.addEventListener('mousedown', this.handleClickOutside);
    }

    componentWillUnmount() {
        document.removeEventListener('mousedown', this.handleClickOutside);
    }
    handleClickOutside(e){
        if(e.target.nodeName !== "BUTTON" && e.target.nodeName !== "INPUT") {
            this.setState({
                filtered_options : []
            })
        }
    }

    autoComplete(e){
        let val = e.target.value;
        // filter options according to supplied filter function
        let filtered_options = this.props.filterFunc? this.props.filterFunc(val, this.state.options) : this.state.filtered_options;

        this.setState({filtered_options})
    }
    render () {
        return (
            <div className={this.props.containerClass || "row"}>
                <div className={this.props.className + "  z-1000 bg-white"}>
                    <label htmlFor={this.props.name} className={this.props.labelClass}>{this.props.caption}</label>
                    <input 
                        type = "text"
                        className={this.props.ctrlClass} 
                        onInput={this.autoComplete}
                        onChange={this.props.onChange}
                        onClick={this.autoComplete}
                        id={this.props.name}
                        name={this.props.name}
                        value={this.props.value}
                        placeholder={this.props.placeholder}               
                        />
                    <span className="muted small">
                        {this.props.help}
                    </span>
                </div>
                <div className={this.props.optionsDropdownClass + " absolute-float"} >
                    {this.props.formatOptions ? this.props.formatOptions(this.state.filtered_options, this.props.onClickElement) : ""}
                </div>
            </div>

        );
    }        
}
export default AutoCompleteTextBox
  
  