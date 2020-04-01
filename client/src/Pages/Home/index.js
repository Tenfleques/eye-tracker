import React from 'react';
import Utils from "../../Utilities/";
import AnimateLoad from "../../HOCS/AnimateLoad";


const Home = AnimateLoad(class Home extends React.Component {
        render () {
            return (
                <div className="">            
                    <div className="container-fluid mt-5">
                        <div className="row">
                            <div className="col-12 h5">
                                {Utils.TextUtils.getLocalCaption("_home_lead")}
                            </div>
                            <div className="col-12">
                                {Utils.TextUtils.getLocalCaption("_description")}
                            </div>
                        </div>
                    </div>
                </div>      
            ); 
        }
    }
)
  
  export default Home;