import { defineStore } from 'pinia'
import { ref } from "vue";
import request from "@/utils/index.js";

const useStore = defineStore('namespace', () => {
    const namespace = ref('');
    const change = val => {
        namespace.value = val;
    }
    request.getNamespace().then(({ data }) => namespace.value = data.namespace);
    return {
        namespace,
        change
    };
});

export default useStore;