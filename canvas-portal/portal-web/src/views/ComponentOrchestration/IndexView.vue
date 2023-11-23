<script setup>
import { ref, onMounted } from "vue";
import { Search, Plus } from '@element-plus/icons-vue';
import request from "@/utils/index.js";
import { formatDate } from "@/utils/utils";
import { showLoading, hideLoading } from '@/utils/loading';
import CreateDialog from '@/components/ComponentInstance/InstanceCreate/IndexView.vue';
const input = ref('');
const tableData = ref([]);
const dialogFormVisible = ref(false);
const requestGridData = async () => {
    try {
        showLoading({ target: '.component-instance' });
        const param = {
            namespace: "components",
            tenantId: 101237,
            keyword: input.value
        }
        const { data } = await request.getOrchestrations(param);
        tableData.value = data.map(o => {
            return {
                ...o,
                createTime: formatDate(o.createTime)
            };
        });
        // console.log(tableData.value);
    } finally {
        hideLoading();
    }
}
// getComponentInstance
onMounted(async () => {
    requestGridData();
});
const searchInstance = () => {
    requestGridData();
}
const viewDetail = (row) => {
    const { name } = row;
    const url = window.location.origin + '/ComponentDetail/' + name;
    window.open(url);
}
const formatRules = (rules) => {
}
</script>
<template>
    <div class="component-instance bg-customFFF p-2">
        <el-row :gutter="20" justify="space-between" align="middle">
            <el-col :span="6">
                <el-input clearable @change="searchInstance" v-model="input" size="default" class="w-50 m-2"
                    placeholder="Please enter the orchestration-name" :suffix-icon="Search" />
            </el-col>
            <el-col :span="18">
                <div class="flex items-center justify-end mr-2">
                    <!-- <el-button>新建实例</el-button> -->
                    <el-button size="default" type="primary" :icon="Plus" @click="dialogFormVisible = true">
                        {{ $t('ODA.CREATE') }}
                    </el-button>
                </div>
            </el-col>
        </el-row>
        <el-row :gutter="20">
            <el-col :span="24">
                <el-table @cell-dblclick="viewDetail" :data="tableData" :header-cell-style="{ color: '#4c4c4c' }"
                    style="width: 100%;" :cell-style="{ color: '#4c4c4c' }">
                    <el-table-column fixed prop="name" :label="$t('ODA.NAME')" show-overflow-tooltip width="250" />
                    <el-table-column prop="rules" :label="$t('ODA.RULES')" show-overflow-tooltip width="360">
                        <template #default="scope">
                            <div v-html="formatRules(scope.row.rules)"></div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="description" :label="$t('ODA.DESCRIPTION')" show-overflow-tooltip>
                    </el-table-column>
                    <el-table-column prop="createDate" :label="$t('ODA.CREATE_TIME')" show-overflow-tooltip width="180">
                        <template v-slot="{ row }">
                            <div v-html="formatDate(row.createDate)"></div>
                        </template>
                    </el-table-column>
                    <el-table-column fixed="right" :label="$t('ODA.OPERATION')" align="center" width="250">
                        <template #default="scope">
                            <el-button link type="primary" @click="viewDetail(scope.row)" size="small">{{ $t('ODA.DETAIL')
                            }}</el-button>
                            <el-button style="color: red;" link type="primary" size="small">{{ $t('ODA.DELETE')
                            }}</el-button>
                        </template>
                    </el-table-column>
                </el-table>
            </el-col>
        </el-row>
        <CreateDialog @close-dialog="dialogFormVisible = false" :dialogFormVisible="dialogFormVisible" />
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