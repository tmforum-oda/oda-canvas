<script setup>
import { ref, onMounted, watch } from "vue";
import request from "@/utils/index";
import MonaCoEditor from '@/components/monacoEditor/IndexView.vue';
// import { showLoading, hideLoading } from '@/utils/loading';
import useStore from '@/stores/namespace';
const namespaceStore = useStore();
const param = {
    namespace: namespaceStore.namespace
};
watch(() => namespaceStore.namespace, val => {
    param.namespace = val;
    getReleaseValues();
});
const props = defineProps({
    release: {
        type: String,
        default: ''
    }
});
const code = ref('');
const options = ref({
    theme: 'vs-dark',
    language: 'yaml'
});
const getReleaseValues = async () => {
    try {
        // showLoading({ target: '.instance-configuration-code-textarea' });
        const { data } = await request.getReleaseValues(props.release, param);
        code.value = data.data;
    } finally {
        // hideLoading();
    }
}
onMounted(() => {
    getReleaseValues();
})
</script>
<template>
    <!-- <div class="editor" ref="editorRef"></div> -->
    <MonaCoEditor class="instance-configuration-code-textarea" height="600px" :options="options" :modelValue="code" />
</template>
<style lang="scss" scoped>
.editor {
    height: 100%;
    width: 100%;
}
</style>