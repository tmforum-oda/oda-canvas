<script setup>
import request from "@/utils/index";
import { onMounted, ref } from "vue";
import { dealApiStatus } from '@/views/ComponentInstance/formatter';
import { showLoading, hideLoading } from '@/utils/loading';
import useStore from '@/stores/namespace';
import MonaCoEditor from '@/components/monacoEditor/IndexView.vue';
const namespaceStore = useStore();
const param = {
    namespace: namespaceStore.namespace
};
const dialogVisible = ref(false);
const yamlDialogTitle = ref('');
const props = defineProps({
    instanceName: {
        type: String,
        default: ''
    }
});
const code = ref('');
const options = ref({
    theme: 'vs-dark',
    language: 'yaml',
    readOnly: true,
    minimap: {
        enabled: true // 小地图
    }
});
const gridData = ref([]);
const loadGrid = async () => {
    try {
        showLoading({ target: '.api-table' });
        const { data } = await request.getComponentApi({
            componentName: props.instanceName,
            ...param,
        });
        gridData.value = data;
        console.log(data);
    } finally {
        hideLoading();
    }
}
const viewYaml = async row => {
    const { data } = await request.getApiYaml(row.metadata.name, param);
    const yaml = data.data;
    code.value = yaml;
    yamlDialogTitle.value = `API|${row.metadata.name}`;
    dialogVisible.value = true;
}
onMounted(() => {
    loadGrid();
});

function handleApi(api) {
    if (api) {
        window.open(api, '_blank');
    }
}
</script>
<template>
    <div>
        <el-row :gutter="20">
            <el-col :span="24">
                <el-table class="font-custom api-table" :data="gridData" :header-cell-style="{ color: '#4c4c4c' }"
                    style="width: 100%;" :cell-style="{ color: '#4c4c4c' }">
                    <el-table-column prop="metadata.name" label="Name" width="350" show-overflow-tooltip />
                    <el-table-column prop="status.apiStatus.url" label="URL" show-overflow-tooltip />
                    <el-table-column prop="status.implementation.ready" width="100" label="status" show-overflow-tooltip>
                        <template #default="scope">
                            <div v-html="dealApiStatus(scope.row.status.implementation.ready)"></div>
                        </template>
                    </el-table-column>
                    <el-table-column fixed="right" label="Operation" prop="status.apiStatus.developerUI" align="center"
                        width="250">
                        <template #default="scope">
                            <el-button link type="primary" @click="handleApi(scope.row.status?.apiStatus?.developerUI)"
                                size="small">{{ $t('ODA.API_DOC') }}</el-button>
                            <el-button @click="viewYaml(scope.row)" link type="primary" size="small">{{ $t('ODA.VIEW_YAML')
                            }}</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
    </div>
    <el-dialog class="api-dialog" width="55%" v-model="dialogVisible" :title="yamlDialogTitle">
        <MonaCoEditor width="100%" height="500px" :options="options" :modelValue="code" />
    </el-dialog>
</template>
<style lang="scss">
.api-table .el-tabs__item {
    padding: 0 15px;
    min-width: 80px;
}

.api-dialog .el-dialog__header {
    padding-top: 5px !important;
}

.api-dialog .el-dialog__body {
    padding-top: 5px !important;
}
</style>