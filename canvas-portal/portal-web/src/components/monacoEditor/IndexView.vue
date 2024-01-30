<script setup>
import { ref, onMounted, computed, watch, onBeforeUnmount } from "vue";
import * as monaco from 'monaco-editor';
// import "monaco-editor/esm/vs/editor/editor.all.js";
// import "monaco-editor/esm/vs/language/json/monaco.contribution";
// import 'monaco-editor/esm/vs/editor/standalone/browser/accessibilityHelp/accessibilityHelp.js';
// import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
// import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker'
// import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker'
// import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'
// import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
// import * as monaco from "monaco-editor/esm/vs/editor/editor.api";
// 使用 - 创建 monacoEditor 对象

const emit = defineEmits(['update:modelValue', 'change']);
const editorRef = ref(); // editor-DOM
const props = defineProps({
    options: {
        type: Object,
        default: () => { }
    },
    height: {
        type: String,
        default: '300px'
    },
    width: {
        type: String,
        default: '100%'
    },
    modelValue: {
        type: String,
        default: null
    }
});
let myEditor;
const defaultOption = ref({
    value: props.modelValue,
    language: 'javascript',
    theme: 'vs-dark',
    autoIndent: false,
    readOnly: true,
    foldingStrategy: 'indentation', // 代码可分小段折叠
    automaticLayout: true, // 自适应布局
    overviewRulerBorder: false, // 不要滚动条的边框
    autoClosingBrackets: true,
    tabSize: 0, // tab 缩进长度
    scrollBeyondLastLine: false,
    // height: 400,
    wordWrap: 'on', // 默认换行
    minimap: {
        enabled: false, // 不要小地图
    },
});

// 结合默认配置和业务端配置
const resolveOption = computed(() => {
    return {
        ...defaultOption.value,
        ...props.options
    };
});

watch(() => props.modelValue, newValue => {
    if (myEditor) {
        const value = myEditor.getValue();
        if (newValue !== value) {
            myEditor.setValue(newValue);
        }
    }

})
const setEditorHeight = () => {
    const model = myEditor.getModel();
    const lineHeight = myEditor.getOption(monaco.editor.EditorOption.lineHeight);
    const lineCount = model.getLineCount();
    const editorHeight = lineHeight * (lineCount + 1);
    editorRef.value.style.height = editorHeight + 'px';
    // myEditor.layout({
    //     height: editorHeight  /* 设置编辑器的高度 */
    // });
}
// 初始化编辑器
const initEditor = () => {
    myEditor = monaco.editor.create(editorRef.value, resolveOption.value);
    myEditor.onDidChangeModelContent(() => {
        const value = myEditor.getValue();
        emit('update:modelValue', value);
    });
}
onMounted(() => {
    initEditor();
});
onBeforeUnmount(() => {
    myEditor.dispose();
});
</script>
<template>
    <div :style="{ height: props.height, width: props.width }" ref="editorRef" class="monaco-editor" role="monaco-editor">
    </div>
</template>
<style scoped>
#container .monaco-scrollable-element::-webkit-scrollbar {
    display: none;
}
</style>