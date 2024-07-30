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
  const { i18n } = useTranslation();
  const [storedLang, setStoredLang] = useLocalStorage<string>({
    key: "auditize-lang",
    getInitialValueInEffect: false,
  });
  const effectiveLang = lang ?? storedLang ?? window.navigator.language;

  useEffect(() => {
    i18n.changeLanguage(effectiveLang);
    setStoredLang(effectiveLang);
  }, [effectiveLang]);

  return (
    <I18nContext.Provider value={{ lang: effectiveLang }}>
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
