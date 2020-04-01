import React from 'react';
import {Link} from 'react-router-dom';
import { useLocation } from "react-router-dom";
import Utils from "../../Utilities"

const NavBar = (props) => {
  let location = useLocation();
  
  document.addEventListener("click", (e) => {
    if(!e.target.classList.contains("dropdown-toggle")){
      let dropdowns = document.getElementsByClassName("dropdown-menu");
      for(let i = 0; i < dropdowns.length; ++i){
        dropdowns[i].classList.remove("show")
      }
    }
  })

  let onToggleDropDownClick = (e) => {
    let target = e.target.id
    let dropdowns = document.getElementsByClassName("dropdown-menu");
    for(let i = 0; i < dropdowns.length; ++i){
      if(dropdowns[i].getAttribute("aria-labelledby") === target){
        dropdowns[i].classList.add("show")
      }else{
        dropdowns[i].classList.remove("show");
      }
    }
  }
  let get_border_color = (a) => {
    switch (a){
      case 2:
        return "border-bottom border-2x border-white";
      case 1:
        return "border-bottom border-2x border-danger";
      default:
        return "border-none"
    }
  }

  let link_class = (active, dropdown_class) => {
    let border = get_border_color(active)

    return "nav-item text-white bg-transparent no-underline " + border + " "+ dropdown_class;
  }
    

  function parseLink(a){
    let chn = ""
    let active = location.pathname === a.link? 1 : 0;
    let id = "link_id_" + Utils.TextUtils.hashCode(a.link)

    let dropdown_class = arguments[1] ? "dropdown-item text-left px-0" : "";
    
    
    if(a.children){
      chn = a.children.map(c => parseLink(c, true))
      for (let i = 0; i < chn.length; ++i){
        if (chn[i].active){ // if any of my children is active then I'm active too 
          active = 2;
        }
      }

      return {
        "active" : active,
        "html" : <span key={id} className="dropdown show">
                  <Link 
                    key={a.link} 
                    className={link_class(active)}
                    onClick={onToggleDropDownClick}
                    to={a.link} >
                {Utils.TextUtils.getLocalCaption(a.caption)}
              </Link>
                &nbsp;
                <span  
                    className="dropdown-toggle text-white"
                    id={id}
                    onClick={onToggleDropDownClick}
                    data-toggle="dropdown" 
                    aria-haspopup="true" 
                    aria-expanded="false">
              </span>
              <div className="dropdown-menu bg-primary px-3 text-left" aria-labelledby={id}>
                {chn.map(c => c.html)}
              </div>
            </span>
      }
    }

    return {
      "active" : active,
      "html" : <span key={id}>
          <Link 
            key={a.link} 
            className={link_class(active, dropdown_class)} 
            to={a.link} >
        {Utils.TextUtils.getLocalCaption(a.caption)}
      </Link>
    </span>}
  }

  return (
    <nav className={"navbar navbar-dark bg-primary fixed-top " + props.className} >
      {props.navs.map((a) => {
        let parsed = parseLink(a);
        return parsed.html
      })}
    </nav>
  );
}

export default NavBar;