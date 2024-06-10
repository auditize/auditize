import i18n from "i18next";
import { createContext, useEffect } from "react";
import { initReactI18next, useTranslation } from "react-i18next";

function initI18n() {
  i18n
    .use(initReactI18next) // passes i18n down to react-i18next
    .init({
      // the translations
      // (tip move them in a JSON file and import them,
      // or even better, manage them via a UI: https://react.i18next.com/guides/multiple-translation-files#manage-your-translations-with-a-management-gui)
      resources: {
        en: {
          translation: {
            menu: {
              management: "Management",
            },
          },
        },
        fr: {
          translation: {
            menu: {
              management: "Gestion",
            },
          },
        },
      },
      fallbackLng: "en",

      interpolation: {
        escapeValue: false, // react already safes from xss => https://www.i18next.com/translation-function/interpolation#unescape
      },
    });
}

initI18n();

const I18nContext = createContext<{}>({});

export function I18nProvider({
  lang,
  children,
}: {
  lang?: string;
  children: React.ReactNode;
}) {
  const { i18n } = useTranslation();
  useEffect(() => {
    if (lang) {
      i18n.changeLanguage(lang);
    }
  }, [lang]);
  return <I18nContext.Provider value={{}}>{children}</I18nContext.Provider>;
}
