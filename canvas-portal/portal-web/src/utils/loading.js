import { ElLoading } from 'element-plus'

let loadingCount = 0;
let loading;

const startLoading = (option = {}) => {
    loading = ElLoading.service({
        lock: true,
        text: 'Loading',
        background: 'rgba(255, 255, 255, 0.8)',
        ...option
    });
};

const endLoading = () => {
    loading.close();
};

export const showLoading = (el) => {
    if (loadingCount === 0) {
        startLoading(el);
    }
    loadingCount += 1;
};

export const hideLoading = () => {
    if (loadingCount <= 0) {
        return;
    }
    loadingCount -= 1;
    if (loadingCount === 0) {
        endLoading();
    }
}