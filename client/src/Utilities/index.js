import TextUtils from "./text"
import AgentUtils from "./agent"

const LoadExternelScript = (url) =>{
    return new Promise(function(resolve, reject) {
      var script = document.createElement('script');
      script.type = 'text/javascript';
      script.async = true;
      script.src = url;
      script.onload = resolve;
      script.onerror = reject;
      script.onreadystatechange=function(){
          if (script.readyState === 'complete') 
            script.onload()
        }

      document.head.appendChild(script);
    })
}

export default {
    TextUtils,
    AgentUtils, 
    LoadExternelScript
}