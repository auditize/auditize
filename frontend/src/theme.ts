import {
  ActionIcon,
  Button,
  createTheme,
  Input,
  MantineColorsTuple,
  rem,
} from "@mantine/core";

// blue used as primary color is #228be6 or HSL 208, 80%, 52%
// Auditize blue is HSL 210, 80%, 52%

const blue210: MantineColorsTuple = [
  "#e5f6ff",
  "#d1e7fe",
  "#a4cdf6",
  "#74b2f0",
  "#4c9aea",
  "#338be7",
  "#2184e7",
  "#0f71ce",
  "#0065ba",
  "#0057a4",
];

export const theme = createTheme({
  colors: {
    blue210,
  },
  primaryColor: "blue210",
  components: {
    Button: Button.extend({
      vars: (_, props) => {
        if (props.size === "sm" || !props.size) {
          return {
            root: {
              "--button-height": rem(32),
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
              "--ai-size": rem(32),
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
            wrapper: { "--input-height": rem(32) },
          };
        }
        return { wrapper: {} };
      },
    }),
  },
});
