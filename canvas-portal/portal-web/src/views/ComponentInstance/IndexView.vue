<script setup>
import { ref, onMounted, computed } from "vue";
import useStore from '@/stores/namespace'
import { Search, Plus } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import request from "@/utils/index.js";
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { formatStatus, formatDomain } from "./formatter";
import { showLoading, hideLoading } from '@/utils/loading';
import CreateDialog from '@/components/ComponentInstance/InstanceCreate/IndexView.vue';
import { useI18n } from "vue-i18n";
const { t } = useI18n();
dayjs.extend(relativeTime);
const namespaceStore = useStore();
const namespace = computed(() => namespaceStore.namespace);
const formParam = {
    release: '',
    chart: '',
    version: '',
    description: '',
    values: '',
    namespace: namespace.value
};
const input = ref('');
const tableData = ref([]);
const mode = ref(true); // true:新建  false:升级
const dialogFormVisible = ref(false); // dialog是否展示
const dialogData = ref(formParam);
const formatDate = (timestamp, format = 'YYYY-MM-DD HH:mm:ss') => dayjs(timestamp).format(format);

// 查询表格数据
const requestGridData = async () => {
    try {
        showLoading({ target: '.component-instance' });
        const { data } = await request.getComponentInstance(input.value ? { keyword: input.value, namespace: namespace.value } : { namespace: namespace.value });
        tableData.value = data.map(o => {
            return {
                ...o,
                createTime: formatDate(o.createTime)
            };
        });
    } finally {
        hideLoading();
    }
}
// getComponentInstance
onMounted(() => {
    requestGridData();
});
const closeDialog = (bol) => {
    dialogFormVisible.value = false;
    bol && requestGridData();
}
const viewDetail = (row) => {
    const { name } = row;
    const url = '#/ComponentDetail/' + name;
    window.open(url);
}
const updateInstance = row => {
    mode.value = false;
    dialogData.value = row;
    dialogFormVisible.value = true;
}
const uninstallInstance = ({ name, release }) => {
    ElMessageBox.confirm(
        `${t('ODA.UNINSTALL_INSTANCE_CONFIRM')} "${name}"?`,
        'Warning',
        {
            confirmButtonText: t('ODA.CONFIRM'),
            cancelButtonText: t('ODA.CANCEL'),
            type: 'warning',
        }
    ).then(async () => {
        try {
            await request.uninstallRelease(release, namespace.value);
            ElMessage({
                type: 'success',
                message: 'Delete completed',
            });
            requestGridData();
        } catch (error) {
            ElMessage({
                type: 'warning',
                message: 'Delete failed',
            });
            throw error;
        }

    })
}
const createInstance = () => {
    mode.value = true;
    dialogData.value = {
        release: '',
        chart: '',
        version: '',
        description: '',
        values: '',
        namespace: namespace.value
    };
    dialogFormVisible.value = true;
}
</script>
<template>
    <div class="component-instance bg-customFFF p-2">
        <el-row :gutter="20" justify="space-between" align="middle">
            <el-col :span="6">
                <el-input clearable @change="requestGridData" v-model="input" size="default" class="w-50 m-2"
                    :placeholder="$t('ODA.INSTANCE_SEARCH_TIP')" :suffix-icon="Search" />
            </el-col>
            <el-col :span="18">
                <div class="flex items-center justify-end mr-2">
                    <!-- <el-button>新建实例</el-button> -->
                    <el-button size="default" type="primary" :icon="Plus" @click="createInstance()">
                        {{ $t('ODA.CREATE_INSTANCE') }}
                    </el-button>
                </div>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-col :span="24">
                <el-table @cell-dblclick="viewDetail" :data="tableData" :header-cell-style="{ color: '#4c4c4c' }"
                    style="width: 100%;" :cell-style="{ color: '#4c4c4c' }">
                    <el-table-column fixed prop="name" :label="$t('ODA.INSTANCE_NAME')" show-overflow-tooltip width="160" />
                    <el-table-column prop="type" :label="$t('ODA.TYPE')" show-overflow-tooltip width="200" />
                    <el-table-column prop="domain" label="Domain" show-overflow-tooltip width="200">
                        <template v-slot="{ row }">
                            <div v-html="formatDomain(row.domain)"></div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="vendor" :label="$t('ODA.VENDOR')" show-overflow-tooltip width="70" />
                    <el-table-column prop="status" :label="$t('ODA.STATUS')" show-overflow-tooltip width="100">
                        <template v-slot="{ row }">
                            <div v-html="formatStatus(row.status)"></div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="version" :label="$t('ODA.VERSION')" show-overflow-tooltip width="80" />
                    <el-table-column prop="description" :label="$t('ODA.DESCRIPTION')" show-overflow-tooltip />
                    <el-table-column prop="createTime" :label="$t('ODA.CREATE_TIME')" show-overflow-tooltip width="130" />
                    <el-table-column fixed="right" :label="$t('ODA.OPERATION')" align="center" width="210">
                        <template #default="scope">
                            <el-button link type="primary" @click="viewDetail(scope.row)" size="small">{{ $t('ODA.DETAIL')
                            }}</el-button>
                            <el-button link type="primary" @click="updateInstance(scope.row)" size="small">{{
                                $t('ODA.UPGRADE') }}</el-button>
                            <el-button link type="primary" @click="uninstallInstance(scope.row)" size="small">{{
                                $t('ODA.DELETE') }}</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
        <CreateDialog :mode="mode" :dialogData="dialogData" @close-dialog="closeDialog"
            :dialogFormVisible="dialogFormVisible" />
    </div>
</template>
  
<style lang="scss" scoped>
.el-row {
    margin-bottom: 20px;
}

.component-instance {
    min-height: calc(100vh - 3rem);
    // calc(100vh - 3rem)
}

.el-row:last-child {
    margin-bottom: 0;
}

.el-col {
    border-radius: 4px;
}

.grid-content {
    border-radius: 4px;
    min-height: 36px;
}
</style>