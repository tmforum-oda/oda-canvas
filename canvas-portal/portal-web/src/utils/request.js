import axios from 'axios';
import { ElMessage } from 'element-plus';

// 开发环境请求统一加上/api/用于转发请求
const baseURL = import.meta.env.DEV ? '/api/' : '';
const service = axios.create({
    timeout: 5000
});

// 请求拦截器
service.interceptors.request.use(config => {
    config.url = `${baseURL}${config.url}`;
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