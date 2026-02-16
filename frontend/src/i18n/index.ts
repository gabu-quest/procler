import { createI18n } from "vue-i18n";
import en from "./locales/en.json";
import ja from "./locales/ja.json";

const STORAGE_KEY = "procler-locale";

function getInitialLocale(): string {
  // Check localStorage first
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && (stored === "en" || stored === "ja")) {
    return stored;
  }

  // Check browser language
  const browserLang = navigator.language.split("-")[0];
  if (browserLang === "ja") {
    return "ja";
  }

  return "en";
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: "en",
  messages: {
    en,
    ja,
  },
});

export function setLocale(locale: string) {
  if (locale === "en" || locale === "ja") {
    i18n.global.locale.value = locale;
    localStorage.setItem(STORAGE_KEY, locale);
  }
}

export function getLocale(): string {
  return i18n.global.locale.value;
}
