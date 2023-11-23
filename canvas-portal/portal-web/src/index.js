
import SvgIcon from './SvgIcon/index.vue';
import { App, Component } from 'vue';
const components = { SvgIcon };
export default {
    install(app: App) {
        Object.keys(components).forEach((key) => {
            app.component(key, components[key]);
        })
    }
}