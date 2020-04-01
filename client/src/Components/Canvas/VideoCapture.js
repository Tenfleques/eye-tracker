import React from 'react';
import Utils from "../../Utilities";
import {Tracker, ZigZag, Wavey} from "../../Helpers/Tracker";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay, faPause, faRecordVinyl} from '@fortawesome/free-solid-svg-icons';


class VideoCapture extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            width: props.width || 800,
            height: props.height || 600,
            frame_rate : 30,
            flip :  true,
            tracker: {
                // object: ["text 1", "text 2"],
                freq : 1000 * .1,
                name : null
            },
            recording: 0, // -1 record, 1 preview
            sessions: []
        }
        this.stream_src = null;
        this.stream_stage = null;

        this.setStream_src = element => {
            this.stream_src = element;
        };

        this.setStream_stage = element => {
            this.stream_stage = element;
        };

        this.paintCanvas = this.paintCanvas.bind(this);
        this.selectRunner = this.selectRunner.bind(this);
    }
    componentDidMount(){
        this.startStream();
    }
    selectRunner(e) {
        const runners = {
            ZigZag : new ZigZag(10, .5),
            Wavey : new Wavey(10)
        }

        let recording = 1;
        if (e.target.id === this.state.tracker.name){ // collect the recordings, second click, third click stop
            if (this.state.recording === -1){
                recording = 0;
            }
            if (this.state.recording === 1){
                recording = -1;
            }
        }
        const runner = runners[e.target.id] ? runners[e.target.id].run : null;
        let tracker = this.state.tracker
        tracker = {
            ...tracker,
            canvas: this.stream_stage,
            fxy : runner,
            name: e.target.id,
        };

        tracker["tracker"] = new Tracker(tracker);

        this.setState({
                tracker,
                recording,
            });
    }
    startStream(){
        const video = this.stream_src;           
        if (navigator.mediaDevices.getUserMedia) {
            // let supportedConstraints = navigator.mediaDevices.getSupportedConstraints();    
            // console.log(supportedConstraints);
            //setInterval(this.randomUpdateTrackerXY, this.state.tracker.freq);
            navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                video.srcObject = stream;
            })
            .catch(function (errr) {
                console.log("Something went wrong!");
            });
        }    
    }
    paintCanvas(){
        let frames = [];

        setInterval(() => {
            const canvas = this.stream_stage;
            const ctx = canvas.getContext("2d");
        
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            ctx.drawImage(this.stream_src, 0, 0, canvas.width, canvas.height);

            if(this.state.recording){
                const point = this.state.tracker.tracker.update();

                if(this.state.recording === -1){ // collecting frames
                    console.log(point);
                    const frame = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    // use darknet to box the eyes only

                    frames.push({point, frame});

                    if(frames.length > this.state.frame_rate * 5){ 
                        // console.log(frames);
                        //  send frames to server every 5 seconds;
                        frames = []; //reset
                    }
                }
            }
            
        }, 1000 / this.state.frame_rate)
        
    }
    getCanvasSettings(){
        return this.state
    }
    getPlayButton(id){
        let cls = "btn btn-transparent border-primary";
        let caption = id;
        if(this.state.tracker.name === id){
            cls = "btn btn-warning border-primary";
            caption = <>
                {id} 
            </>
            if (this.state.recording === -1){
                cls = "btn btn-success border-primary";
                caption = <>
                {id} <FontAwesomeIcon icon={faRecordVinyl} className="text-primary"/>
            </> 
            }
        }
        return <button className={cls} id={id} onClick={this.selectRunner}>
                    {caption}
                </button>;
    }
    render () {
        return (
            <div className="row">
                <div className="col-12 border-right border-primary border-2x py-0">
                    <h5 className="col-12">
                        {Utils.TextUtils.getLocalCaption("_click_tracker")}
                    </h5>
                    <div className="btn-group my-3">
                        {this.getPlayButton("ZigZag")}
                        {this.getPlayButton("Wavey")}
                        {this.getPlayButton("Random")}
                    </div>

                    <canvas
                        width={this.state.width} 
                        height={this.state.height} 
                        ref={this.setStream_stage}
                        className="">
                    </canvas>
                    
                    <video 
                        ref={this.setStream_src}
                        className="invisible"
                        height="1"
                        onPlay={this.paintCanvas}
                        autoPlay>
                    </video>
                </div>
            </div>
        ); 
    }
}
export default VideoCapture;