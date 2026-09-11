import { createBrowserRouter } from 'react-router'

import AppShell from '../components/AppShell'
import HomeView from '../features/home/HomeView'

const router = createBrowserRouter(
  [
    {
      path: '/',
      Component: AppShell,
      children: [
        {
          index: true,
          Component: HomeView,
        },
      ],
    },
  ],
  {
    basename: import.meta.env.BASE_URL,
  },
)

export default router
