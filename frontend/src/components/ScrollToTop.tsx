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

  return (
    <Affix position={{ bottom: 15, right: 20 }}>
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
