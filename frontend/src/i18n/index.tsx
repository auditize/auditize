import { useLocalStorage } from "@mantine/hooks";
import i18n from "i18next";
import { createContext, useContext, useEffect } from "react";
import { initReactI18next, useTranslation } from "react-i18next";

import translationsEN from "./en";
import translationsFR from "./fr";

function initI18n() {
  i18n
    .use(initReactI18next) // passes i18n down to react-i18next
    .init({
      resources: {
        en: {
          translation: translationsEN,
        },
        fr: {
          translation: translationsFR,
        },
      },
      fallbackLng: "en",

      interpolation: {
        escapeValue: false, // react already safes from xss => https://www.i18next.com/translation-function/interpolation#unescape
      },
    });
}

initI18n();

const I18nContext = createContext<{ lang: string } | null>(null);

export function I18nProvider({
  lang,
  children,
}: {
  lang?: string;
  children: React.ReactNode;
}) {
  // Algorithm to determine the language:
  // 1. If lang is provided (coming from /users/me), use it.
  // 2. If lang is not provided (the user is not authenticated),
  //    use the last known user language previously saved in local storage
  // 3. If the last language is not available, use the browser language.
  const { i18n } = useTranslation();
  const [defaultLang, setDefaultLang] = useLocalStorage<string>({
    key: "auditize-default-lang",
    defaultValue: window.navigator.language,
  });
  useEffect(() => {
    if (lang) {
      i18n.changeLanguage(lang);
      setDefaultLang(lang);
    } else {
      i18n.changeLanguage(defaultLang);
    }
  }, [lang, defaultLang]);
  return (
    <I18nContext.Provider value={{ lang: lang ?? defaultLang }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18nContext() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18nContext must be used within an I18nProvider");
  }
  return context;
}
