import { Center, Group, Menu } from "@mantine/core";
import { IconChevronDown } from "@tabler/icons-react";
import React from "react";
import { NavLink, useLocation } from "react-router-dom";

import classes from "./Navbar.module.css";

type NavbarItemProps = {
  label: string;
  url: string;
  condition?: boolean;
};

export function NavbarItem({ label, url, condition }: NavbarItemProps) {
  if (condition === false) {
    return null;
  }
  return (
    <NavLink
      to={url}
      className={({ isActive }) =>
        isActive ? `${classes.link} ${classes.active}` : classes.link
      }
    >
      {label}
    </NavLink>
  );
}

type NavbarItemGroupProps = {
  label: string;
  children:
    | React.ReactElement<NavbarItemProps>
    | React.ReactElement<NavbarItemProps>[];
};

export function NavbarItemGroup({ label, children }: NavbarItemGroupProps) {
  const location = useLocation();

  // Make sure children is an array
  if (!Array.isArray(children)) {
    children = [children];
  }

  // Check if there is at least one item to be displayed
  if (!children.some((child) => child.props.condition !== false)) {
    return null;
  }

  // Check if the group is active
  const isActive = children.some(
    (child) => location.pathname === child.props.url,
  );

  return (
    <Menu trigger="hover" transitionProps={{ exitDuration: 0 }} withinPortal>
      <Menu.Target>
        <Center>
          <span
            className={
              isActive ? `${classes.link} ${classes.active}` : classes.link
            }
          >
            {label}
          </span>
          <IconChevronDown size="0.9rem" stroke={1.5} />
        </Center>
      </Menu.Target>
      <Menu.Dropdown>
        {React.Children.map(
          children,
          (child) =>
            child.props.condition !== false && (
              <Menu.Item
                component={NavLink}
                to={child.props.url}
                className={
                  location.pathname === child.props.url
                    ? `${classes.link} ${classes.active}`
                    : classes.link
                }
              >
                {child.props.label}
              </Menu.Item>
            ),
        )}
      </Menu.Dropdown>
    </Menu>
  );
}

export function Navbar({
  children,
}: {
  children:
    | React.ReactElement<NavbarItemProps | NavbarItemGroupProps>
    | React.ReactElement<NavbarItemProps | NavbarItemGroupProps>[];
}) {
  return <Group gap={0}>{children}</Group>;
}