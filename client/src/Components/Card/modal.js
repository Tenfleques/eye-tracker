import React from 'react';
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {faTimesCircle} from '@fortawesome/free-solid-svg-icons';

class Modal extends React.Component{
    constructor(props){
        super(props);
        this.state = {
            show_modal : false,
        }
        this.toggleModal = this.toggleModal.bind(this);
    }
    toggleModal(){
        this.setState({show_modal: !this.state.show_modal});
    }
    getstyle(){
        if (this.state.show_modal)
            return {display:"block"}
    }
    render(){
        return <>
            <button 
                type="button" 
                className={this.props.buttonClass || "btn btn-primary"} 
                onClick={this.toggleModal}>
                    {this.props.caption || "..."}
            </button>

            <div className={"modal fade " + (this.state.show_modal ? " show" : "")} tabIndex="-1" role="dialog"   style={this.getstyle()}>
                <div className="modal-dialog modal-lg">
                    <div className="modal-content p-1">
                        <div className="col-12 text-right">
                            <button 
                                type="button" 
                                className="btn btn-transparent"
                                onClick={this.toggleModal}>
                                    <FontAwesomeIcon icon={faTimesCircle} className="text-danger"/>
                            </button>
                        </div>
                        <div className="p-3">
                            {this.props.children}
                        </div>
                    </div>
                </div>
            </div>
        </>
    }
}

export default Modal;