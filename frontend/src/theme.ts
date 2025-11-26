import {
  ActionIcon,
  Button,
  createTheme,
  Input,
  MantineColorsTuple,
  Pagination,
  rem,
  ScrollArea,
} from "@mantine/core";

// Default Mantine blue used as a primary color is #228be6 or HSL 208, 80%, 52%.
// Blue defined by Auditize (blue Crayola) is HSL 214, 80%, 52%.
// Palette generated with https://mantine.dev/colors-generator/?color=2378E7

const BLUE_214: MantineColorsTuple = [
  "#e6f5ff",
  "#d1e5fe",
  "#a4c8f6",
  "#74aaf0",
  "#4b90ea",
  "#327fe7",
  "#2177e7",
  "#1065ce",
  "#005aba",
  "#004da4",
];

const INPUT_HEIGHT = rem(32);

export const theme = createTheme({
  cursorType: "pointer", // https://mantine.dev/core/switch/#pointer-cursor
  colors: {
    blue214: BLUE_214,
  },
  primaryColor: "blue214",
  components: {
    Button: Button.extend({
      vars: (_, props) => {
        if (props.size === "sm" || !props.size) {
          return {
            root: {
              "--button-height": INPUT_HEIGHT,
              "--button-padding-x": rem(14),
            },
          };
        }
        return { root: {} };
      },
    }),
    ActionIcon: ActionIcon.extend({
      vars: (_, props) => {
        if (props.size === "input-sm") {
          return {
            root: {
              "--ai-size": INPUT_HEIGHT,
            },
          };
        }
        return { root: {} };
      },
    }),
    Pagination: Pagination.extend({
      vars: (_, props) => {
        if (props.size === "sm" || !props.size) {
          return {
            root: {
              "--pagination-control-size": rem(28),
              "--pagination-control-fz": rem(14),
            },
          };
        }
        return { root: {} };
      },
    }),
    Input: Input.extend({
      vars: (_, props) => {
        if (props.size === "sm" || !props.size) {
          return {
            wrapper: { "--input-height": INPUT_HEIGHT },
          };
        }
        return { wrapper: {} };
      },
    }),
    ScrollArea: ScrollArea.extend({
      vars: () => {
        return {
          root: {
            "--scrollarea-scrollbar-size": rem(6),
          },
        };
      },
    }),
  },
});
