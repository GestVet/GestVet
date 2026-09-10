import { createBrowserRouter } from 'react-router'

import App from '../App'
import HomeView from '../features/home/HomeView'

const router = createBrowserRouter(
  [
    {
      path: '/',
      Component: App,
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
