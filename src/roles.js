// DEMO ONLY: these credentials are checked in the browser and are visible to anyone
// who opens the site's JavaScript. Replace roleLogin() in RoleLogin.jsx with a real
// backend call before using this for anything that needs actual protection.
export const ROLES = {
  maintainer: {
    label: "Maintainer",
    title: "Maintainer tools",
    subtitle: "Review and correct derived metadata while preserving original source values.",
    username: "maintainer",
    password: "maintainer123",
  },
  admin: {
    label: "Administration",
    title: "Administration",
    subtitle: "Repository sources, system health, roles, and privileged activity.",
    username: "admin",
    password: "admin123",
  },
};
