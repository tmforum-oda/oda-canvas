<script setup>
import { ref, computed, watch, toRef } from 'vue';
import request from "@/utils/index.js";
import { useI18n } from 'vue-i18n';
import useStore from '@/stores/namespace'
const { t } = useI18n();
import MonaCoEditor from '@/components/monacoEditor/IndexView.vue';
const namespaceStore = useStore();
const namespace = computed(() => namespaceStore.namespace);
const param = {
    namespace: namespace.value
};
const props = defineProps({
    dialogFormVisible: {
        type: Boolean,
        default: false
    },
    mode: {
        type: Boolean,
        default: true
    },
    dialogData: {
        type: Object,
        default: {
            release: '',
            chart: '',
            version: '',
            description: '',
            values: '',
            namespace: ''
        }
    },
    formLabelWidth: {
        type: String,
        default: '120px'
    }
});
const ruleForm = toRef(props.dialogData);
const chartData = ref([]);
const versionData = ref([]);
const code = ref('');
const options = ref({
    theme: 'vs-dark',
    language: 'yaml',
    readOnly: false
});
const rules = ref({
    release: [
        { required: true, message: t('ODA.CANNOT_EMPTY'), trigger: 'blur' },
        { pattern: /^[a-z0-9-]+$/, message: t('ODA.LOWER_NUMBER'), trigger: 'blur' }
    ],
    chart: [
        { required: true, message: t('ODA.CANNOT_EMPTY'), trigger: 'blur' }
    ],
    version: [
        { required: true, message: t('ODA.CANNOT_EMPTY'), trigger: 'change' }
    ],

});
watch(() => code.value, () => {
    ruleForm.value.values = code.value;
})
watch(() => props.dialogData, val => {
    ruleForm.value = val;
});
watch(() => props.dialogFormVisible, val => {
    val && getCharts(); // 每次dialog显现时重新加载charts
    code.value = '';
})

const getCharts = async () => {
    try {
        const { data = [] } = await request.getCharts(param);
        chartData.value = data;
        if (props.dialogData.release) {
            const { data } = await request.getReleaseDetailInfo(props.dialogData.release, param);
            const { repoName, chartName, chartVersion } = data;
            ruleForm.value.chart = repoName + '/' + chartName;
            await changeChart(ruleForm.value.chart);
            changeVersion(chartVersion);
        }
    } catch (error) {
        chartData.value = [];
    }

}

const emit = defineEmits(['close-dialog']);
// onMounted(() => {
//     getCharts();
// })
const createInstance = async () => {
    const parameter = ruleForm.value;
    await request.installRelease(parameter);
    emit('close-dialog', true);
}
const changeVersion = async version => {
    if (!version || version === '') {
        code.value = '';
        return;
    }
    const tarVersion = versionData.value.find(o => o.version === version);
    if (!tarVersion) {
        return;
    }
    const { repoName, chartName, version: targetVersion } = tarVersion;
    const { data } = await request.getChartValues(repoName, chartName, targetVersion);
    code.value = data.data;
}

// chart改变的回调
const changeChart = async name => {
    ruleForm.value.version = '';
    if (name === '') {
        versionData.value = [];
        return;
    }
    const obj = chartData.value.find(o => o.name === name);
    if (!obj) {
        versionData.value = [];
        return;
    }
    const { data = [] } = await request.getChartVersions(obj.repoName, obj.chartName, param);

    versionData.value = data;
    ruleForm.value.version = obj.version;
    return true;
}
</script>
<template>
    <el-dialog class="create-isntance-dialog" destroy-on-close :close-on-click-modal="false" :draggable="true"
        @close="emit('close-dialog', false)" :model-value="props.dialogFormVisible"
        :title="props.mode ? $t('ODA.NEW_INSTANCE') : $t('ODA.UPGRADE_INSTANCE')">
        <el-form label-position="right" label-width="80px" @submit.prevent :model="ruleForm" :rules="rules">
            <el-collapse :model-value="['1', '2']">
                <el-collapse-item :title="$t('ODA.BASIC_INFORMATION')" name="1">
                    <template #title><span class="pl-5">{{ $t('ODA.BASIC_INFORMATION') }}</span><el-icon
                            class="header-icon"></el-icon></template>
                    <el-form-item :label="$t('ODA.NAME') + ':'" :label-width="formLabelWidth" prop="release">
                        <el-input size="small" :disabled="!props.mode" :placeholder="$t('ODA.LOWER_NUMBER')"
                            v-model="ruleForm.release" clearable />
                    </el-form-item>
                    <el-form-item :label="$t('ODA.ODA_COMPONENT') + ':'" :label-width="formLabelWidth" prop="chart">
                        <el-select @change="changeChart" v-model="ruleForm.chart" :placeholder="$t('ODA.SELECT_COMPONENT')"
                            clearable>
                            <el-option v-for="item in chartData" :key="item.name" :label="item.name" :value="item.name"
                                :title="item.description" />
                        </el-select>
                    </el-form-item>
                    <el-form-item :label="$t('ODA.VERSION') + ':'" :label-width="formLabelWidth" prop="type">
                        <el-select @change="changeVersion" v-model="ruleForm.version"
                            :placeholder="$t('ODA.SELECT_VERSION')" clearable>
                            <el-option v-for="item in versionData" :key="item.version" :label="item.version"
                                :value="item.version">
                                <template #default>
                                    <span>{{ `Chart Version: ${item.version} / Component Version: ${item.app_version}`
                                    }}</span>
                                </template>
                            </el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item :label="$t('ODA.DESCRIPTION') + ':'" :label-width="formLabelWidth" prop="description">
                        <el-input :autosize="{ minRows: 4, maxRows: 8 }" v-model="ruleForm.description" type="textarea"
                            clearable />
                    </el-form-item>
                </el-collapse-item>
                <el-collapse-item :title="$t('ODA.INSTANCE_CONFIGURATION')" name="2">
                    <template #title><span class="pl-5">{{ $t('ODA.INSTANCE_CONFIGURATION') }}</span><el-icon
                            class="header-icon"></el-icon></template>
                    <el-form-item label-width="50px" prop="content">
                        <div style="height: 350px;width: 100%;border: 1px solid #eee;">
                            <MonaCoEditor width="100%" height="350px" :options="options" :modelValue="code" />
                        </div>
                    </el-form-item>
                </el-collapse-item>
            </el-collapse>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button size="default" type="primary" @click="createInstance()">{{ $t('ODA.OK') }}</el-button>
                <el-button size="default" @click="emit('close-dialog')">{{ $t('ODA.CANCEL') }}</el-button>
            </span>
        </template>
    </el-dialog>
</template>

<style lang="scss">
.create-isntance-dialog {
    height: 500px;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .el-dialog__body {
        padding: 10px 20px;
        flex: 1;
        overflow-y: auto;

        .el-collapse {
            border-top: none;

            .el-collapse-item__header {
                height: 32px;
                line-height: 32px;
                font-size: 15px;
                border-bottom: 1px solid var(--el-collapse-border-color);
            }

            .el-collapse-item__header::before {
                content: " ";
                margin-top: 2px;
                float: left;
                width: 5px;
                height: 18px;
                border-left: 5px solid #00a1ea;
                display: block;
            }

            .el-collapse-item__header:hover {
                background-color: #f5f5f5;
            }

            .el-collapse-item__content {
                margin-top: 10px;
                padding-bottom: 0;
            }

            .el-collapse-item__wrap {
                border: none;
            }
        }


        .el-select {
            width: 100%;
        }

        .el-form-item__content {
            padding-right: 40px;
        }
    }
}
</style>
