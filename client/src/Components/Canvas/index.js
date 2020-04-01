import React from 'react';
import Utils from "../../utilities";
import AnimateLoad from "../../HOCS/AnimateLoad";
import Colors from "../../Configs/Constants/colors";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleDoubleLeft, faAngleDoubleRight, faSave} from '@fortawesome/free-solid-svg-icons';
import Select from "../../Controls/Select";


const HexColors = Colors.map(col => col[1]);
// object in image is defined by label, bound box [x1 , y1 , x2, y2]
const AnnotationPage = AnimateLoad(class AnnotationPage extends React.Component {
        constructor(props){
            super(props);
            this.state = {
                images :  [{
                        src : "images/examples/IMG_20190814_193414.jpg",
                        objects : [
                        ],
                        active : 0
                    },{
                        src : "images/examples/IMG_20190806_194139.jpg",   // example image for testing
                        objects : [
                        ],
                        active: 0
                    }
                ],
                active : 1,
                scale : 1.0,
                y_offset : 180,
                ctrls : {
                    image_width : 512,
                    image_height : 512,
                },
                history : {
                    current: 0,
                    objects : []
                },
                active_object : {
                    xmin : null,
                    ymin : null,
                    xmax : null,
                    ymax : null,
                    height : null,
                    width : null,
                    name : ""
                },
                datasets : [

                ],
                isDragging :  false,
                dragxy : {
                    x : null,
                    y : null
                },
                current_dataset : ""
            }
            this.drawImage = this.drawImage.bind(this);
            // this.onChangeSizeCtrl = this.onChangeSizeCtrl.bind(this);
            this.onChangeLabelCtrl = this.onChangeLabelCtrl.bind(this);
            this.onCanvasMouseDown = this.onCanvasMouseDown.bind(this)
            this.onUndo = this.onUndo.bind(this);
            this.onNextImage = this.onNextImage.bind(this);
            this.onSavelabel = this.onSavelabel.bind(this);
            this.onSaveSession = this.onSaveSession.bind(this);
            this.onMouseDown = this.onMouseDown.bind(this);
            this.onMouseMove = this.onMouseMove.bind(this);
            this.onMouseUp = this.onMouseUp.bind(this);
            this.changeClickYOffset = this.changeClickYOffset.bind(this);
        }
        drawImage(){
            var img = new Image();
            img.crossOrigin = "Anonymous";
            img.onload = (me) => { 
                const canvas = this.refs.annotation_stage;
                const ctx = canvas.getContext("2d");

                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                let scale =this.state.ctrls.image_height/me.target.naturalHeight;
                let w = me.target.naturalWidth * scale;
                let h = me.target.naturalHeight * scale;

                canvas.width = w;
                canvas.height = h;

                ctx.drawImage(me.target, 
                    0, 0, me.target.width, me.target.height,
                    0, 0, w, h);
                
                let active_objects = this.state.images[this.state.active].objects;
                
                for (let i = 0; i < active_objects.length; i++){
                    this.boundBox(ctx, active_objects[i], i)
                }
                if(this.state.scale !== scale
                    || this.state.ctrls.image_height !== h
                    || this.state.ctrls.image_width !== w){
                    let ctrls = this.state.ctrls;
                    ctrls.image_height = h;
                    ctrls.image_width = w;
                    this.setState({ctrls, scale}, () => {
                        // console.log(this.state.ctrls, canvas.width)
                    });
                }
            }
            img.onerror = (er, e) => {
                console.log(er, e)
            }
            
            img.src =  this.state.images[this.state.active].src
        }
        componentDidMount(){
            console.log(Utils.GDrive);
            document.addEventListener("keydown", (e) => {
                if (e.keyCode === 90 && (e.ctrlKey || e.metaKey)){
                    this.onUndo();
                }
            })
        }
        onSaveSession(){
            let images = this.state.images;
            let url = "";
            fetch(url, {
                body : images,
                method : "post"
            })
            .then(res => res.json())
            .then(res => {
                console.log(res);
            })
            .catch(err => {
                console.log(err);
            })
        }
        getImages(){
            let ds = this.state.current_dataset;
            let url = "?dataset=" + ds;
            fetch(url, {
                method : "get"
            })
            .then(res => res.json())
            .then(images => {
                this.setState({images})
            })
            .catch(err => {
                console.log(err);
            })
        }
        getDatasets(){
            let url = "";
            fetch(url, {
                method : "get"
            })
            .then(res => res.json())
            .then(datasets => {
                let current_dataset = datasets[0].value
                this.setState({datasets, current_dataset})
            })
            .catch(err => {
                console.log(err);
            })
        }
        onChangeLabelCtrl(e){ // e can be event or string literal
            let active_object = this.state.active_object;
            active_object.name = e.target ? e.target.value : e;
            this.setState({active_object});
        }
        boundBox(ctx, box, index){
            ctx.strokeStyle = this.getColor(index);
            ctx.fillStyle = this.getColor(index);
            let drawPoint = (x, y) => {
                ctx.beginPath();
                ctx.moveTo(x, y);
                ctx.arc(x, y , 2, 0, 2 * Math.PI);
                ctx.fill();
                ctx.closePath();
            }
            if(box.xmin !== null 
                && box.ymin !== null
                && box.xmax !== null
                && box.ymax !== null){
                ctx.beginPath();
                ctx.moveTo(box.xmin, box.ymin);
                ctx.rect(box.xmin, box.ymin, box.xmax - box.xmin, box.ymax - box.ymin);
                ctx.stroke();
                ctx.closePath();
                ctx.font = "14px Comic Sans MS";
                ctx.textAlign = "left";
                ctx.fillText(box.name, Math.min(...[box.xmin, box.xmax]) + 5,Math.min(...[box.ymin, box.ymax]) + 15);


            }else if(box.xmin !== null
                    && box.ymin !== null){
                    drawPoint(box.xmin, box.ymin);
                if(box.xmax !== null){
                    drawPoint(box.xmax, box.ymin);
                }else if(box.ymax !== null){
                    drawPoint(box.xmin, box.ymax);
                }
            }
        }
        getColor(index){
            if(index === undefined){
                let active_image = this.state.images[this.state.active];
                index = active_image.objects.length - 1;
            }
            index %= HexColors.length;
            return HexColors[index];
        }
        onSavelabel(){
            let images = this.state.images;
            images[this.state.active].active += 1;
            let history = {
                current: 0,
                objects : []
            }
            let active_object = {
                xmin : null,
                ymin : null,
                xmax : null,
                ymax : null,
                height : null,
                width : null,
                name : ""
            }
            const next = JSON.parse(JSON.stringify(active_object));
            images[this.state.active].objects.push(next);
            this.setState({images, history, active_object});
        }
        onUndo(){
            let history = this.state.history;
            if(history.current > 0){
                history.current -= 1;
                let active_object = history.objects[history.current];
                let images = this.state.images;
                const active_index = images[this.state.active].active;
                images[this.state.active].objects[active_index] = active_object;
                this.setState({active_object, images, history});
            }
        }
        onNextImage(rev = false){
            let history = {
                current: 0,
                objects : []
            }
            let active_object = {
                xmin : null,
                ymin : null,
                xmax : null,
                ymax : null,
                height : null,
                width : null,
                name : ""
            }
            let active = this.state.active;
            if (rev){
                active -= 1;
            }else{
                active += 1
            }
            if (active < 0){
                active = this.state.images.length - 1;
            }
            if (active > this.state.images.length - 1){
                active = 0;
            }
            this.setState({history, active, active_object});
        }
        isSetActiveBox(){
            return this.state.active_object.xmin 
                    && this.state.active_object.xmax 
                    && this.state.active_object.ymin 
                    && this.state.active_object.ymax
        }
        insideActiveBox(x,y){
            return (this.state.active_object.xmin  <= x 
                        && this.state.active_object.xmax >= x )
                    && (this.state.active_object.ymin  <= y && this.state.active_object.ymax >= y )

        }
        onCanvasMouseDown(e){
            const pos_x = e.clientX - e.target.offsetLeft;
            const pos_y = e.clientY - this.state.y_offset;

            let images = this.state.images;
            const active_index = images[this.state.active].active;

            let active_object = JSON.parse(JSON.stringify(this.state.active_object));
            let prev_object = images[this.state.active].objects[active_index] || JSON.parse(JSON.stringify(active_object));

            let updated = false;

            if(active_object.xmin === null
                || active_object.ymin === null){
                active_object.xmin = pos_x;
                active_object.ymin = pos_y;
                updated = true;
            }else {
                // choose the large distance in y or x
                if (Math.abs(active_object.xmin - pos_x) < Math.abs(active_object.ymin - pos_y)){ // update y first
                    if(active_object.ymax === null){
                        active_object.ymax = pos_y;
                        updated = true;
                    }else if(active_object.xmax === null){
                        active_object.xmax = pos_x;
                        updated = true
                    }
                }else{ // update x first
                    if(active_object.xmax === null){
                        active_object.xmax = pos_x;
                        updated = true
                    }else if(active_object.ymax === null){
                        active_object.ymax = pos_y;
                        updated = true;
                    }
                }
            }
            if(updated){

                let history = this.state.history;

                if(history.current < history.objects.length){
                    history.objects[history.current] = prev_object;
                }else{
                    history.objects.push(prev_object);
                }
                history.current += 1;

                const active_index = images[this.state.active].active;
                images[this.state.active].objects[active_index] = active_object;

                this.setState({active_object, images, history});
            }
        }
        onMouseDown(e){
            const x = e.clientX - e.target.offsetLeft;
            const y = e.clientY - this.state.y_offset;
            if (this.isSetActiveBox()){ // initialize box dragging
                if(this.insideActiveBox(x,y)){
                    const dragxy = {
                        x,
                        y
                    }
                    this.setState({isDragging: true, dragxy});
                }else{
                    console.log("click outside the box", x, y );
                }
            }else{
                this.onCanvasMouseDown(e);
            }
        }
        onMouseMove(e){
            if (this.state.isDragging){
                const x = e.clientX - e.target.offsetLeft;
                const y = e.clientY - this.state.y_offset;
                const dragxy = this.state.dragxy;

                if (dragxy.x === null){
                    dragxy.x = x;
                }
                if (dragxy.y === null ){
                    dragxy.y = y;
                }
                const dx = dragxy.x - x;
                const dy = dragxy.y - y;

                const active_object = this.state.active_object;

                active_object.xmin -= dx;
                active_object.xmax -= dx;

                active_object.ymin -= dy;
                active_object.ymax -= dy;

                
                dragxy.x = x;
                dragxy.y = y;
                this.setState({active_object, dragxy});
            }
        }
        onMouseUp(){
            if(this.state.isDragging){
                const dragxy = {
                    x : null,
                    y : null
                };
                this.setState({isDragging : false});
            }
        }
        changeClickYOffset(e){
            const y_offset = e.target.value;
            this.setState({y_offset});
        }
        getSaveButton() {
            if (this.state.active_object.name
                && this.isSetActiveBox()){
                return <button 
                            onClick={this.onSavelabel}
                            className="btn btn-transparent border-primary">
                                {Utils.TextUtils.getLocalCaption("_save")}
                        </button>
            }
            return <button 
                    className="btn invisible">
                </button>;
        }
        getUsedLabels(){
            let labels = [];
            let images = this.state.images;
            let label_list = [];
            const ready = this.isSetActiveBox();

            images.map(img => {
                return img.objects.map(obj => {
                    if (!labels.includes(obj.name)){
                        labels.push(obj.name);
                        label_list.push(<h6 
                                    key={obj.name}
                                    onClick={() => {
                                        if(ready){
                                            this.onChangeLabelCtrl(obj.name);
                                            this.onSavelabel();
                                        }
                                    }}
                                    className={(!ready?"disabled text-light" : "text-primary") + " col-12 mouse-pointer"}>
                                    {obj.name}
                            </h6>);
                    }
                    return obj
                })
            });
            return <div className="row px-3">
                    <div className="border-top col-12 py-3 px-0">
                        <h6 className="mb-2">
                            {Utils.TextUtils.getLocalCaption("_used_labels")}
                        </h6>
                        {label_list}
                    </div>
                </div>;
        }
        render () {
            this.drawImage();
            return (
                <div className="">            
                    <div className="container-fluid mt-5">
                        <div className="row">
                            <div className="col-12">
                                <h5>{Utils.TextUtils.getLocalCaption("_image_annotation")}</h5>
                                <div className="settings-panel row">
                                    <div className="text-left col">
                                        <Select 
                                            name="select_dataset"
                                            labelClass="py-2 h6"
                                            caption={Utils.TextUtils.getLocalCaption("_select_dataset")}
                                            options={this.state.datasets}
                                            />
                                        <div className="form-group d-none">
                                            <label htmlFor="image_height">{Utils.TextUtils.getLocalCaption("_image_height_ctrl_label")}</label>
                                            <input 
                                                type="number" 
                                                className="form-control" 
                                                name = "image_height" 
                                                id = "image_height"
                                                readOnly={true}
                                                // onChange={this.onChangeSizeCtrl} 
                                                value={this.state.ctrls.image_height}/>
                                        </div>
                                    </div>
                                    <div className="text-right col">
                                        <div className="form-group">
                                            <label
                                                className="py-2 h6"
                                                htmlFor="click-y_offset">
                                                {Utils.TextUtils.getLocalCaption("_click_canvas_y_offset")}
                                            </label>
                                            <input 
                                                id="click-y_offset"
                                                className="form-control" 
                                                value={this.state.y_offset} 
                                                type="number" 
                                                onChange={this.changeClickYOffset}/>
                                        </div>
                                        
                                    </div>
                                    <div className="text-right col mt-4 pt-3">
                                        <button 
                                            onClick={() => this.onNextImage(true)}
                                            className="btn btn-transparent border-primary mr-1 text-primary mt-1">
                                                <FontAwesomeIcon icon={faAngleDoubleLeft}/>
                                                &nbsp;
                                                {Utils.TextUtils.getLocalCaption("_prev")}
                                        </button>
                                        <button 
                                            onClick={() => this.onSaveSession()}
                                            className="btn btn-transparent border-primary mr-1 text-primary mt-1">
                                                <FontAwesomeIcon icon={faSave}/>
                                                &nbsp;
                                                {Utils.TextUtils.getLocalCaption("_save")}
                                        </button>                                        
                                        <button 
                                            onClick={() => this.onNextImage(false)}
                                            className="btn btn-transparent border-primary mt-1">
                                                {Utils.TextUtils.getLocalCaption("_next")}
                                                &nbsp;
                                                <FontAwesomeIcon icon={faAngleDoubleRight}/>
                                        </button>
                                    </div>
                                </div>
                                <div className="row">
                                    <div className="col-12 col-md-9 col-lg-8 border-right border-primary border-2x py-0">
                                        <canvas
                                            onMouseDown={this.onMouseDown}
                                            onMouseUp={this.onMouseUp}
                                            onMouseMove={this.onMouseMove}
                                            width={this.state.ctrls.image_width} 
                                            height={this.state.ctrls.image_height}
                                            ref="annotation_stage" 
                                            className="">
                                        </canvas>
                                    </div>
                                    <div className="d-none d-md-block col-md-3 col-lg-4 py-0">
                                        <div className="form-group">
                                            <h6 htmlFor="image_height">{Utils.TextUtils.getLocalCaption("_image_labels")}</h6>
                                            <input 
                                                type="text" 
                                                className="form-control mb-3" 
                                                name = "image_height" 
                                                id = "image_height"
                                                onChange={this.onChangeLabelCtrl} 
                                                value={this.state.active_object.name}/>
                                            {this.getSaveButton()}
                                        </div>
                                        <div className="labels-list">
                                            {this.getUsedLabels()}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>      
            ); 
        }
    }
)
  
  export default AnnotationPage;