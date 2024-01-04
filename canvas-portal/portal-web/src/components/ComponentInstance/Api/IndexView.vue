<script setup>
import request from "@/utils/index";
import { onMounted, ref } from "vue";
import { dealApiStatus } from '@/views/ComponentInstance/formatter';
import { showLoading, hideLoading } from '@/utils/loading';
import useStore from '@/stores/namespace';
const namespaceStore = useStore();
const param = {
    namespace: namespaceStore.namespace
};
const props = defineProps({
    instanceName: {
        type: String,
        default: ''
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
onMounted(() => {
    loadGrid();
})
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
                            <el-button link type="primary" size="small">{{ $t('ODA.VIEW_YAML') }}</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
    </div>
</template>
<style lang="scss" scoped>
.el-tabs__item {
    padding: 0 15px;
    min-width: 80px;
}
</style>