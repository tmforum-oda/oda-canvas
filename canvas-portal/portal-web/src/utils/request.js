import axios from 'axios';
import { ElMessage } from 'element-plus';
const service = axios.create({
    timeout: 5000
});
// 请求拦截器
service.interceptors.request.use(config => {
    return config;
}, error => {
    Promise.reject(error);
});

service.interceptors.response.use(response => {
    return response;
}, error => {
    if (error.response && error.response.data) {
        const { code, message } = error.response.data;
        if (code && message) {
            ElMessage.error(`${code}:${message}`);
        } else {
            try {
                const msg = JSON.stringify(error.response.data);
                ElMessage.error(msg);
            } catch (error) {
                // ElMessage.error();
            }
        }
    } else {
        try {
            const msg = JSON.stringify(error.response.data);
            ElMessage.error(msg);
        } catch (error) {
            // ElMessage.error();
        }
    }
    return Promise.reject(error);
});

export default service;