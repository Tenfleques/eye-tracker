import React from 'react';
import Utils from "../../Utilities";
import AnimateLoad from "../../HOCS/AnimateLoad";
import Modal from "../../Components/Card/modal";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {faArrowRight, faArrowLeft} from '@fortawesome/free-solid-svg-icons';
import VideoCapture from "../../Components/Canvas/VideoCapture";
import Tracker from "../../Components/Card/Tracker";

const DataCollection = AnimateLoad(class Page extends React.Component {
        constructor(props){
            super(props);
            this.state = {
                document: {
                    subject : {

                    },
                    experiments : [

                    ]
                },
                settingsCollapsed: false,
            }
            this.toggleSettingsBar = this.toggleSettingsBar.bind(this);
        }
        getSettingsPane(){
            return <>
                {/* <Tracker /> */}
             </>
        }
        toggleSettingsBar(){
            this.setState({settingsCollapsed: !this.state.settingsCollapsed})
        }
        render () {
            return (
                <div className="">            
                    <div className="container-fluid mt-5">
                        <div className="row">
                            <div className="col-12 d-lg-none">
                                {/* settings invoked on click modal for small device */}
                                <Modal>
                                    <h5>
                                        {Utils.TextUtils.getLocalCaption("_settings")}
                                    </h5>
                                    {this.getSettingsPane()}
                                </Modal>
                            </div>
                            <div className={"col-12 " + (this.state.settingsCollapsed? "col-lg-11" : "col-lg-8")} >
                                <VideoCapture />
                            </div>
                            <div className={"d-none d-lg-block " + (this.state.settingsCollapsed? "col-lg-1" : "col-lg-4")}>
                                <h5>
                                    {/* <button className="btn btn-transparent text-left" onClick={this.toggleSettingsBar}>
                                        <FontAwesomeIcon icon={this.state.settingsCollapsed? faArrowLeft : faArrowRight} />
                                    </button> */}
                                    {!this.state.settingsCollapsed && Utils.TextUtils.getLocalCaption("_settings")}
                                </h5>
                                
                                {this.getSettingsPane()}
                            </div>
                        </div>
                    </div>
                </div>      
            ); 
        }
    }
)
  
  export default DataCollection;