import { createI18n } from "vue-i18n";
import { getLanguage } from '@/utils/cookies';
import zh from '@/locals/zh';
import en from '@/locals/en';

const currentLanguage = getLanguage();
const messages = { en, zh };
const systemLanguage = (navigator.language || navigator.browserLanguage).toLowerCase();
const locale = currentLanguage || systemLanguage.split('-')[0] || 'en';
const i18n = createI18n({
    legacy: false,
    locale,
    fallbackLocale: 'en',
    messages
});

export default i18n;