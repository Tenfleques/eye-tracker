import React, {Component} from "react";


class Table extends Component {
    constructor (props){
        super(props);
        this.state = {
            columns : props.columns,
            data : props.data,
            title: props.title,
            page : 0, 
            rows : props.rows
        }
        this.onClickPagination = this.onClickPagination.bind(this);
    }
    getColumns(){
        var columns = <div className={this.props.headerClass  + ' z-200 sticky-columns text-center'}>
                        <div className='row px-3'>
                            <div className="col-12 h6 text-left">
                               {this.props.title || ""} 
                            </div>
                            {
                                this.state.columns.map((c) => {
                                    return <div key={"col_" + c.field} className={c.class + ' col '}>
                                        {c.title}
                                    </div>
                                })
                            }
                        </div>
                    </div>
        return columns;
    }
    getRows(){
        var rows = [];
        let cls = "";
        let init = this.state.page * this.state.rows;
        let end = Math.min(init + this.state.rows, this.state.data.length);


        for(var i = init; i < end;  ++i){       
            rows.push(
                <div key={"row_" +  i} className={cls + ' row px-3'}>
                {this.state.columns.map((j) => {
                    return  <div key={"cell_" + j.field} className={j.class + ' col'}>    
                            {this.state.data[i][j.field]}
                        </div>
                    })
                }                 
            </div>
            );
        }
        rows.push(<div key={"row_pagination"} className={cls + ' row py-2 px-3 '}> {this.getPagination()}</div>)
        return rows;
    }
    onClickPagination(page){
        this.setState({page : page});
    }
    getPagination(){
        let pages = Math.floor(this.state.data.length/ this.state.rows) + (this.state.data.length % this.state.rows ? 1 : 0);

        let btns = [];
        if (pages < 2){
            return "";
        }
        for(let i = 0; i < pages; ++i){
            btns.push(
                <span key={"page_" + i} className={"btn btn-transparent mx-0 text-muted text-small" + (this.state.page === i ? " bg-primary text-white" : "")} onClick={() => this.onClickPagination(i)}>
                    {i + 1}
                </span>
            )
        }
        return btns;
    }
    componentDidUpdate(oldProps){
        if(this.props !== oldProps){
            this.setState({
                columns : this.props.columns,
                data : this.props.data,
                title: this.props.title,
            })
        }
    }
    render(){
        var columns = this.getColumns();
        var rows = this.getRows();
    
        return <div className={this.props.className}>
                    {columns}
                    {rows}
                </div>
    }
}

export default Table