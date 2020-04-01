class Tracker {
    constructor(props){
        this.state = {
            canvas: props.canvas,
            x : props.x || 0,
            y : props.y || 0,
            w : props.w || 10,
            h : props.h || 10,
            object : props.object,
            object_index : 0,
            history: [], 
            fxy :  props.fxy,
            freq : props.freq || 1000 * 5, // update position every second
        }
        this.update = this.update;
        this.getHistory = () => this.state.history;
    }
    cycleIndex(index, arr){
        const l = arr.length;
        if (index > l - 2){
            return 0;
        }
        return index + 1;
    }
    update(){
        const l = this.state.history.length;
        const date = new Date().getTime();
        if(l){            
            const last_entry = this.state.history[l - 1];
            if (date - last_entry.date > this.state.freq){
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
                // history.push(hist_obj);
                history[0] = hist_obj;
                this.state.x  = xy.x;
                this.state.y = xy.y;
                this.state.history = history;

                if (Array.isArray(this.state.object)){
                    let index = this.state.object_index;
                    this.state.object_index = this.cycleIndex(index, this.state.object);
                }
            }
        }else{
            this.state.x  = 0;
            this.state.y = 0;
            this.state.history = [
                {
                    x : 0,
                    y : 0,
                    date
                }
            ];
        }

        const ctx = this.state.canvas.getContext("2d");
        ctx.strokeStyle = 'rgb(255, 0, 0)';
        ctx.fillStyle = 'rgb(255, 0, 0)';

        if (Array.isArray(this.state.object)){
            ctx.font = '18px serif';
            ctx.fillText(this.state.object[this.state.object_index], this.state.x, this.state.y);
            
        }else{
            ctx.fillRect(this.state.x, this.state.y, this.state.w, this.state.h);
        }
        return {
            x : this.state.x,
            y : this.state.y
        }
    }
}

class ZigZag {
    /** given x, y, returns new x,y in the range 0,w and 0,h respectively, x step increments, y = ax + c */
    constructor(step=10 ,a = .5, c = 3, grad_inc = .1) {
        this.run = (x, y, w, h) => {
            if ( x + step <= 0 || x + step >= w){ // flip step
                step *= -1;
                a += grad_inc
            }
            if(a >= 1){
                grad_inc *= -1;
                a += grad_inc;
            }
            y = Math.abs(a*x + c);
            const diff = y - h;
            if (diff > 0){
                a *= -1;
            }
            y = Math.abs(a*x + c);
            x += step;
            
            return {
                x,
                y
            }
        }
    }    
}
class Wavey {
    /** given x, y, returns new x,y in the range 0,w and 0,h respectively, x step increments, y = asin(x + c), */
    constructor(step=10, p =.1) {
        this.run = (x, y, w, h) => {
            if ( x + step <= 0 || x + step >= w){ // flip step
                step *= -1;
                p += .1
                if(p > 1){
                    p = .1;
                }
            }
            y = h * Math.sin((p * x/w) * Math.PI) ;
            x += step;
            
            return {
                x,
                y
            }
        }
    }    
}

export {
    Tracker,
    ZigZag, 
    Wavey
};