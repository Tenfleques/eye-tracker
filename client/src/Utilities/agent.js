const getAgentLocale = () => {
    let lang = localStorage.getItem("_locale") || navigator.language || navigator.userLanguage || "ru";
    return lang.slice(0,2);
}


const AgentUtils = {
    getAgentLocale
}

export default AgentUtils;