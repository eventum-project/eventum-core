// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  gettingStartedSidebar: [
    {
      type: 'doc',
      id: 'getting_started/overview/index'
    },
    {
      type: 'doc',
      id: 'getting_started/installation/index'
    }
  ],
  pluginsSidebar: [
    {
      type: 'category',
      label: 'Plugins',
      collapsible: true,
      collapsed: false,
      link: {
        type: 'doc',
        id: 'plugins/index'
      },
      items: [
        {
          type: 'category',
          label: 'Input plugins',
          collapsible: true,
          collapsed: false,
          link: {
            type: 'doc',
            id: 'plugins/index'
          },
          items: []
        },
        {
          type: 'category',
          label: 'Event plugins',
          collapsible: true,
          collapsed: false,
          link: {
            type: 'doc',
            id: 'plugins/index'
          },
          items: []
        },
        {
          type: 'category',
          label: 'Output plugins',
          collapsible: true,
          collapsed: false,
          link: {
            type: 'doc',
            id: 'plugins/index'
          },
          items: []
        },
      ]
    },
  ]
};

export default sidebars;
