import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import translationEN from './locales/en/translation.json';
import translationKO from './locales/ko/translation.json';
import translationRU from './locales/ru/translation.json';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: translationEN },
    ko: { translation: translationKO },
    ru: { translation: translationRU }
  },
  lng: localStorage.getItem('app_language') || 'ko',
  fallbackLng: 'en',
  interpolation: { escapeValue: false }
});

export default i18n;
