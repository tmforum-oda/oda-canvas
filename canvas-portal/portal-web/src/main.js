import './assets/main.css';
import '@/main.css';
import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import { createPinia } from 'pinia';
import 'element-plus/dist/index.css';
import App from './App.vue';
import router from './router';
import request from "@/utils/request";
import svgIcon from "@/components/SvgIcon/index.vue";
import 'virtual:svg-icons-register';
import i18n from '@/locals';

const pinia = createPinia();
const app = createApp(App);

app.config.errorHandler = (err, vm, info) => {
    // handle error
    console.log('err', err);
}
app.config.globalProperties.$request = request;
app.use(router)
    .use(pinia)
    .use(i18n)
    .use(ElementPlus, { size: 'small', zIndex: 3000 })
    .component('svgIcon', svgIcon);

// 导航异步加载
router.isReady().then(() => {
    // router.beforeEach((to, from, next) => {
    //     next();
    // });
    // router.afterEach((to, from) => {
    // });
    app.mount('#app');
}); 
