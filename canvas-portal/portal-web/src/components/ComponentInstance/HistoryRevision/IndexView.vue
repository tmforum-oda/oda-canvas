<script setup>
import request from "@/utils/index";
import { onMounted, ref } from "vue";
import { ElMessage } from 'element-plus';
import { formatDate } from '@/utils/utils';
import { showLoading, hideLoading } from '@/utils/loading';
import useStore from '@/stores/namespace';
const namespaceStore = useStore();
const param = {
    namespace: namespaceStore.namespace
};
const props = defineProps({
    release: {
        type: String,
        default: ''
    }
});
const gridData = ref([]);
const currentRevision = ref('');
const showMgs = () => {
    ElMessage({
        message: 'Release not exist, failed to query history revision!',
        type: 'warning',
    });
};
const getReleaseDetailInfo = async () => {
    return await request.getReleaseDetailInfo(props.release, param);
}
const getReleaseVersion = async () => {
    return await request.getReleaseVersion(props.release, param);
}
const loadGrid = async () => {
    try {
        showLoading({ target: '.revision-table' });
        const { data: detail } = await getReleaseDetailInfo();
        const revision = detail?.revision;
        currentRevision.value = revision;
        if (!revision) {
            showMgs();
            return;
        }
        const { data: versions } = await getReleaseVersion();
        gridData.value = versions;
    } catch (error) {
        showMgs();
    } finally {
        hideLoading();
    }
}
onMounted(() => {
    loadGrid();
});
const handleVersion = (revision) => {
    if (revision === currentRevision.value) {
        return `${revision} <span class="label" style="color: #5cb85c;border: 1px solid #5cb85c;border-radius:6px;margin-left:5px;display: inline;padding: 0.2em 0.6em 0.3em;font-size: 75%;font-weight: 700;line-height: 1;text-align: center;white-space: nowrap;vertical-align: baseline;border-radius: 0.25em;color: #5cb85c;border: 1px solid #5cb85c;border-radius: 6px;margin-left: 5px;">Current</span>`;
    }
    return revision;
}

</script>
<template>
    <div>
        <el-row :gutter="20">
            <el-col :span="24">
                <el-table class="font-custom revision-table" :data="gridData" :header-cell-style="{ color: '#4c4c4c' }"
                    style="width: 100%;" :cell-style="{ color: '#4c4c4c' }">
                    <el-table-column prop="revision" label="Revision" width="350" show-overflow-tooltip>
                        <template v-slot="{ row }">
                            <span v-html="handleVersion(row.revision)"></span>
                            <!-- <span>`if (cellVal === ts.currentRevision) return 
                            return cellVal;`</span> -->
                        </template>
                    </el-table-column>
                    <el-table-column prop="updated" label="Updated Time" show-overflow-tooltip>
                        <template v-slot="{ row }">
                            {{ formatDate(row.updated) }}
                        </template>
                    </el-table-column>
                    <el-table-column prop="app_version" width="100" label="Version" show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column prop="chart" label="Chart" show-overflow-tooltip />
                    <el-table-column prop="description" label="Description" show-overflow-tooltip />
                    <el-table-column fixed="right" label="Operation" align="center" width="250">
                        <template #default="scope">
                            <el-button link type="primary" @click="handle()" size="small">Instance Configuration</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
    </div>
</template>