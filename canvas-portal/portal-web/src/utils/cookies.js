import Cookies from 'js-cookie';
const languageKey = 'LOCALE';
export const getLanguage = () => Cookies.get(languageKey);
export const setLanguage = language => Cookies.set(languageKey, language);