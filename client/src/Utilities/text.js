import Locale from "../_locale"
import AgentUtils from "./agent"

const hashCode = function(str) {
    var hash = 0, i, chr;
    if (str.length === 0) return hash;
    for (i = 0; i < str.length; i++) {
      chr   = str.charCodeAt(i);
      hash  = ((hash << 5) - hash) + chr;
      hash |= 0; // Convert to 32bit integer
    }
    return Math.abs(hash);
};

function getLocalCaption(key){
    const user_lang = AgentUtils.getAgentLocale();
    if (Locale[user_lang][key]){
        return Locale[user_lang][key].title
    }

    if (Locale["en"][key]){
        return Locale["en"][key].title
    }

    return "";
}

const TextUtilities = {
    hashCode,
    getLocalCaption
}
export default TextUtilities;