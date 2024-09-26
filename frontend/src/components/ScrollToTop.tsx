import { Affix, Button, Transition } from "@mantine/core";
import { useViewportSize, useWindowScroll } from "@mantine/hooks";
import { IconArrowUp } from "@tabler/icons-react";
import { useTranslation } from "react-i18next";

import { iconSize } from "@/utils/ui";

// borrowed from https://mantine.dev/core/affix/
export function ScrollToTop() {
  const { height: viewportHeight } = useViewportSize();
  const [scroll, scrollTo] = useWindowScroll();
  const { t } = useTranslation();

  // NB: set zIndex to 100 instead of the default 200 to avoid displaying the button
  // at the exact same level as modals (the log detail modal for example)
  return (
    <Affix position={{ bottom: 15, right: 20 }} zIndex={100}>
      <Transition transition="slide-up" mounted={scroll.y > viewportHeight}>
        {(transitionStyles) => (
          <Button
            onClick={() => scrollTo({ y: 0 })}
            leftSection={<IconArrowUp style={iconSize(16)} />}
            style={transitionStyles}
            variant="default"
            size="xs"
          >
            {t("common.scrollToTop")}
          </Button>
        )}
      </Transition>
    </Affix>
  );
}
