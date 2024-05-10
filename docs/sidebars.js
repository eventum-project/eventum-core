// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  gettingStartedSidebar: [
    {
      type: 'category',
      label: 'Overview',
      collapsible: true,
      collapsed: false,
      link: {
        type: 'doc',
        id: 'overview/index'
      },
      items: [
        {
          type: 'doc',
          id: 'overview/templates/index'
        }
      ]
    },
    {
      type: 'category',
      label: 'Installation',
      collapsible: true,
      collapsed: false,
      link: {
        type: 'doc',
        id: 'overview/index'
      },
      items: [
        {
          type: 'doc',
          id: 'overview/templates/index'
        }
      ]
    }
  ],
};

export default sidebars;
