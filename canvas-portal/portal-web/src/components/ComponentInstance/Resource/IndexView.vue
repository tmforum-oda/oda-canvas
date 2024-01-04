<script setup>
import request from "@/utils/index";
import { onMounted, ref } from "vue";
import { formatDate as format } from '@/utils/utils'
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { showLoading, hideLoading } from '@/utils/loading';
dayjs.extend(relativeTime);
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
        showLoading({ target: '.resource-table' });
        const { data } = await request.getComponentResources(props.instanceName, param);
        console.log(data);
        gridData.value = data;
    } finally {
        hideLoading();
    }
}
onMounted(() => {
    loadGrid();
})
</script>
<template>
    <div>
        <el-row :gutter="20">
            <el-col :span="24">
                <el-table class="font-custom resource-table" :data="gridData" :header-cell-style="{ color: '#4c4c4c' }"
                    style="width: 100%;" :cell-style="{ color: '#4c4c4c' }">
                    <el-table-column prop="metadata.name" :label="$t('ODA.RESOURCE_NAME')" width="" show-overflow-tooltip />
                    <el-table-column prop="kind" :label="$t('ODA.TYPE')" show-overflow-tooltip />
                    <el-table-column prop="metadata.creationTimestamp" width="" :label="$t('ODA.CREATE_TIME')"
                        show-overflow-tooltip>
                        <template v-slot="{ row }">
                            {{ format(row.metadata.creationTimestamp) }}
                        </template>
                    </el-table-column>
                    <el-table-column fixed="right" :label="$t('ODA.OPERATION')" align="center" width="250">
                        <template #default>
                            <el-button link type="primary" size="small">{{ $t('ODA.VIEW_YAML') }}</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
    </div>
</template>
