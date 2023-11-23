<script setup>
import request from "@/utils/index";
import useStore from '@/stores/namespace'
import { onMounted, ref, watch, computed } from "vue";
import { formatDomain, formatStatus } from "@/views/ComponentInstance/formatter";
import ApiView from '@/components/ComponentInstance/Api/IndexView.vue';
import ResourceView from '@/components/ComponentInstance/Resource/IndexView.vue';
import ConfigurationView from '@/components/ComponentInstance/InstanceConfiguration/IndexView.vue';
import HistoryRevision from '@/components/ComponentInstance/HistoryRevision/IndexView.vue';
import { formatDate } from '@/utils/utils';
import { Loading } from '@element-plus/icons-vue';
import { showLoading, hideLoading } from '@/utils/loading';
const namespaceStore = useStore();
const INSTANCE_NAME = location.hash.replace('#/ComponentDetail/', '');
const info = ref({});
const instanceEvents = ref([]);
const chartVersion = ref({});
const release = ref('');
const activeName = ref('first');
const loading = ref(true);
const param = {
    namespace: namespaceStore.namespace
};
const renderDetail = async () => {
    try {
        showLoading({ target: '.info-detail' });
        const { data } = await request.getInstanceDetail(INSTANCE_NAME, param);
        info.value = data;
        // 如果查询到的release不存在
        if (!data.release) loading.value = false;
        release.value = data.release;
        // console.log(info);
    } catch {
        loading.value = false;
    } finally {
        hideLoading();
    }
}
const renderInstanceEvents = async () => {
    try {
        showLoading({ target: '.instance-wrap' });
        const { data } = await request.getInstanceEvents(INSTANCE_NAME, param);
        instanceEvents.value = data;
    } finally {
        hideLoading();
    }
}
watch(() => {
    return info.value.release;
}, async (newValue) => {
    if (newValue && info.value.release) {
        const { data } = await request.getReleaseDetailInfo(info.value.release, param);
        loading.value = false;
        // console.log('data:', data);
        chartVersion.value = data;
    }
});
onMounted(() => {
    renderDetail();
    renderInstanceEvents();
})
// console.log(INSTANCE_NAME);


</script>
<template>
    <div class="bg-customFFF text-black text-xs font-lighter info-detail" style="padding: 15px 20px 20px;">
        <el-row :gutter="10">
            <el-col class="text-left text-label" :span="10">
                <h3 class="text-lg text-labelVal">{{ $t('ODA.BASIC_INFORMATION') }}</h3>
            </el-col>
            <el-col class="text-right text-label" :span="14">
                <el-button style="font-size: 14px;margin-top: 4px;" class="text-right" type="primary" link>{{
                    $t('ODA.VIEW_YAML') }}</el-button>
            </el-col>
        </el-row>

        <div class="wrapper mt-8">
            <el-row :gutter="10">
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.NAME') }}：</el-col>
                <el-col class="text-labelVal" :span="10">{{ info.name }}</el-col>
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.NAMESPACE') }}：</el-col>
                <el-col class="text-labelVal" :span="10">{{ info.namespace }}</el-col>
            </el-row>
            <el-row :gutter="10">
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.VERSION') }}：</el-col>
                <el-col class="text-labelVal" :span="10">{{ info.version }}</el-col>
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.TYPE') }}：</el-col>
                <el-col class="text-labelVal" :span="10">{{ info.type }}</el-col>
            </el-row>
            <el-row :gutter="10">
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.CHART_VERSION') }}：</el-col>
                <el-col class="text-labelVal" :span="10" v-if="loading">
                    <el-icon :size="16" class="is-loading">
                        <Loading />
                    </el-icon>
                </el-col>
                <!-- <el-col class="text-labelVal" :span="10" v-if="loading">
                    <SvgIcon name="spinner" color="#3b82f6" class="animate-spin w-4 h-4 fill-blue-400" />
                </el-col> -->
                <el-col class="text-labelVal" :span="10" v-else-if="!loading && chartVersion.chart">
                    <el-button style="font-size: 13px;margin-top: -2px;border: none;" type="primary" link>{{
                        chartVersion.chart }}</el-button>
                </el-col>
                <el-col class="text-labelVal" :span="10" v-else><span style="color: orange">release not
                        exist</span></el-col>
                <el-col class="text-right text-label" :span="2">Domain：</el-col>
                <el-col class="text-labelVal" :span="10" v-html="formatDomain(info.domain)"></el-col>
            </el-row>
            <el-row :gutter="10">
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.STATUS') }}：</el-col>
                <el-col class="text-labelVal" :span="10" v-html="formatStatus(info.status)"></el-col>
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.VENDOR') }}：</el-col>
                <el-col class="text-labelVal" :span="10">{{ info.release }}</el-col>
            </el-row>
            <el-row :gutter="10">
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.DESCRIPTION') }}：</el-col>
                <el-col class="text-labelVal" :span="10">{{ info.description }}</el-col>
                <el-col class="text-right text-label" :span="2">{{ $t('ODA.CREATE_TIME') }}：</el-col>
                <el-col class="text-labelVal" :span="10">{{ formatDate(info.createTime) }}</el-col>
            </el-row>
        </div>

    </div>
    <div class="bg-customFFF mt-4" style="padding: 15px 10px 20px 20px;">
        <el-row :gutter="10">
            <el-col class="text-left text-label" :span="10">
                <h3 class="text-lg text-labelVal">{{ $t('ODA.EVENT') }}</h3>
            </el-col>
        </el-row>
        <div class="wrapper instance-wrap mt-4" style="overflow-y: scroll;max-height: 400px;color: #646464;">
            <div v-if="instanceEvents.length !== 0">
                <div v-for="(item, index) in instanceEvents" :key="index">
                    <div class="oda-event-item">
                        <div>
                            <div v-if="item.type === 'Error'">
                                <div class="oda-event-item-icon"
                                    style="box-shadow: 0 0 2px 3px #ffc476;background-color: #F4920F;">
                                </div>
                            </div>
                            <div v-else>
                                <div class="oda-event-item-icon"
                                    style="box-shadow: 0 0 2px 3px #bbc5d8 ;background-color: #3D7FFF;"></div>
                            </div>
                            <span class="oda-event-item-state">
                                {{ item.reason }}
                            </span>
                            <span class="oda-event-item-label">
                                {{ item.involvedObject.name }}
                            </span>
                            <span class="oda-event-item-time">
                                {{ formatDate(item.eventTime) }}
                            </span>
                        </div>
                        <div>
                            {{ item.message }}
                        </div>
                    </div>
                </div>
            </div>
            <div class="text-center" v-else>No Data</div>
        </div>
    </div>
    <div class="bg-customFFF mt-4" style="padding: 15px 20px 20px;">
        <el-tabs v-model="activeName" class="demo-tabs">
            <el-tab-pane label="API" name="first">
                <ApiView :instanceName="INSTANCE_NAME" />
            </el-tab-pane>
            <el-tab-pane lazy :label="$t('ODA.RESOURCE')" name="second">
                <ResourceView :instanceName="INSTANCE_NAME" />
            </el-tab-pane>
            <el-tab-pane lazy :label="$t('ODA.INSTANCE_CONFIGURATION')" name="third">
                <ConfigurationView :release="release" :instanceName="INSTANCE_NAME" />
            </el-tab-pane>
            <el-tab-pane lazy :label="$t('ODA.HISTORY_REVISION')" name="fourth">
                <HistoryRevision :release="release" />
            </el-tab-pane>
        </el-tabs>
    </div>
</template>
<style>
.demo-tabs>.el-tabs__content {
    padding: 32px;
    color: #6b778c;
    font-size: 32px;
    font-weight: 600;
}

.wrapper {
    font-size: 13px;
    font-family: Helvetica Neue, Helvetica, PingFang SC, Hiragino Sans GB, Microsoft YaHei, \\5FAE\8F6F\96C5\9ED1, Arial, sans-serif;
}

.el-row {
    margin-bottom: 10px;
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

.oda-event-item {
    border-bottom: 1px solid #eee;
    margin: 30px 28px 0 28px;
}

.oda-event-item>div:first-child {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    position: relative;
}

.oda-event-item>div:nth-child(2) {
    font-size: 12px;
    color: #acaeb4;
    font-weight: 400;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 14px;
}

.oda-event-item-icon {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    position: absolute;
    top: 0;
    bottom: 0;
    margin: auto 0;
    left: -20px;
}

.oda-event-item-state {
    display: inline-block;
    background: #F3F6FC;
    border: 1px solid rgba(225, 229, 235, 1);
    border-radius: 2px;
    margin-right: 6px;
    padding: 0 5px;
}

.oda-event-item-label {
    font-size: 14px;
    color: #333;
    font-weight: bold;
    flex-grow: 1;
}

.oda-event-item-time {
    font-size: 12px;
    color: #999;
    font-weight: 400;
}
</style>