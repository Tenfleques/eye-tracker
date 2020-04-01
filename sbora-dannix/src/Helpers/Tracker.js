class Tracker {
    constructor(props){
        this.state = {
            canvas: props.canvas,
            x : props.x || 0,
            y : props.y || 0,
            w : props.w || 10,
            h : props.h || 10,
            history: [], 
            freq : props.freq || 1000 * 5, // update position every second
        }
        this.update = this.update;
    }
    update(){
        const l = this.state.history.length;
        const date = new Date().getTime();
        // if(l){            
        //     const last_entry = this.state.history[l - 1];
        //     if (date - last_entry.date > this.state.freq){
        //         return;
        //     }
        // }
        let xy;
        if (this.state.fxy){
            xy = this.state.fxy(this.state.x, this.state.y, this.state.canvas.width, this.state.canvas.height)
        }else{
            const x = Math.floor(Math.random() * 1000)%this.state.canvas.width
            const y = Math.floor(Math.random() * 1000)%this.state.canvas.height;
            xy = {x, y };
        }
        const history = this.state.history;
        const hist_obj = {
            ...xy,
            date
        }
        history.push(hist_obj);

        // this.state.x  = xy.x;
        // this.state.y = xy.y;
        // this.state.history = history;

        // console.log(history);
                
        // const ctx = this.state.canvas.getContext("2d");
        // ctx.fillStyle = 'rgb(255, 0, 0)';
        // ctx.strokeStyle = 'rgb(0, 0, 255)';
        // ctx.fillRect(this.state.x, this.state.y, this.state.w, this.state.h);
    }
}
export default Tracker;