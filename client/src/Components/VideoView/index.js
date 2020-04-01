import React, {Component} from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faHome} from '@fortawesome/free-solid-svg-icons'

class ImageCarousel extends Component{
    constructor(props) {
        super(props)
        this.state = {
            root : props.root,
            images: props.images
        }
    }
    componentDidUpdate(prevProps){
        if(JSON.stringify(prevProps) !== JSON.stringify(this.props)){
            this.setState({root : this.props.root, images : this.props.images})
        }
    }
    onClickDir(path){
        this.props.onClickDir(path);
        this.setState({root : path});
    }
    
    showFileList(){
        if (this.state.images){            
                                  
        }
        return "";
    }


    render(){

        return (<div className={this.props.className} >
                    Image carousel                 
                </div>);        
    }
}

export default FileList;