import React from 'react';

const InfoCard = (props) => {
    return (
        <div className={props.className} >
            <span className="Title h4 py-3">
                {props.title}
            </span>
            <div className="row py-3">
                <div className="col-12"> 
                    {props.content}
                </div>
            </div>            
        </div>
    );
}

export default InfoCard;