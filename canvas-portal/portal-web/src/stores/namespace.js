import { defineStore } from 'pinia'
import { ref } from 'vue';
import request from "@/utils/index.js";

const useStore = defineStore('namespace', () => {
    // dataSource给顶层使用,namespace给内部使用,
    const dataSource = ref([]);
    const namespace = ref('');
    request.getNamespace().then(({ data = [] }) => {
        dataSource.value[0] = data;
        // namespace.value = data[0]; // namespace默认第一个
        namespace.value = data[0];
    });
    const change = val => {
        namespace.value = val;
    }
    // request.getNamespace().then(({ data }) => namespace.value = data.namespace);
    return {
        namespace,
        dataSource,
        change
    };
});

export default useStore;