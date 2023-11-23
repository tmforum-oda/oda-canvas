import { createRouter, createWebHashHistory } from 'vue-router'
import ComponentStatus from '@/views/ComponentStatus/IndexView.vue'
const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/componentInstance' },
    {
      // 组件状态
      path: '/componentStatus',
      name: 'componentStatus',
      component: ComponentStatus
    },
    {
      // 组件地图
      path: '/componentMap',
      name: 'ComponentMap',
      component: () => import('@/views/ComponentMap/IndexView.vue')
    },
    {
      // 组件实例
      path: '/componentInstance',
      name: 'ComponentInstance',
      component: () => import('@/views/ComponentInstance/IndexView.vue'),
    },
    {
      // 组件详情
      path: '/componentDetail/:name',
      name: 'ComponentDetail',
      component: () => import('@/views/ComponentDetail/IndexView.vue'),
      meta: {
        hideNav: true
      }
    },
    {
      // 组件兼容性测试
      path: '/componentComplianceTest',
      name: 'ComponentComplianceTest',
      component: () => import('@/views/ComponentComplianceTest/IndexView.vue')
    },
    {
      // 编排
      path: '/componentOrchestration',
      name: 'ComponentOrchestration',
      component: () => import('@/views/ComponentOrchestration/IndexView.vue')
    },
    {
      path: '/:pathMatch(.*)',
      redirect: '/'
    }
  ]
});

export default router
