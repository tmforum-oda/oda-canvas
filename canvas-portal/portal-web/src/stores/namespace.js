import { defineStore } from 'pinia'
import { ref } from 'vue';
import request from "@/utils/index.js";

const useStore = defineStore('namespace', () => {
    // dataSource给顶层使用,namespace给内部使用,
    const dataSource = ref([]);
    const namespace = ref('');
    request.getNamespace().then(({ data = [] }) => {
        dataSource.value = data;
        namespace.value = data[0];
    });
    const change = val => {
        namespace.value = val;
    }
    return {
        namespace,
        dataSource,
        change
    };
});

export default useStore;