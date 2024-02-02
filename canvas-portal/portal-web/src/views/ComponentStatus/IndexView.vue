<script setup>
import { onMounted, computed, ref } from 'vue';
import useStore from '@/stores/namespace';
import TopBg from "@/components/ComponentStatus/TopBg.vue";
import OdaComponent from "@/components/ComponentStatus/OdaComponents.vue";
import ComponentInstance from "@/components/ComponentStatus/ComponentInstance.vue";
import ODACanvasService from "@/components/ComponentStatus/ODACanvasService.vue";
import { chunk } from 'lodash-es';
import request from '@/utils/index';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
dayjs.extend(relativeTime);
const formatDate = (timestamp, format = 'YYYY-MM-DD HH:mm:ss') => dayjs(timestamp).format(format);

const namespaceStore = useStore();
const namespace = computed(() => namespaceStore.namespace);
const maxPolygon = ref(0);
const showComponent = ref(false);

const componentList = ref([]);
const instanceList = ref([]);
onMounted(() => {
    getComponents();
});
const getComponents = async () => {
    const { data } = await request.getComponents({
        namespace: namespace.value
    }) || [];
    resolveChunkData(data);
}

const instanceTrigger = list => {
    const resList = [...(chunk(list, 4))];
    instanceList.value = resList;
}

const resolveChunkData = data => {
    let allInstances = [];
    const colorMap = {
        Production: '#179287',
        Engagement_Management: '#D97A0B ',
        Core_Commerce_Management: '#763BC4',
        Decoupling_and_Integration: '#3484f5',
        Party_Management: '#8acc42',
        Intelligence_Management: '#215AB0'
    };
    data.forEach(o => {
        o.color = colorMap[o.domain.split(' ').join('_')]; // 指定每个组件的颜色
        if (o.types.length && maxPolygon.value < o.types.length) {
            maxPolygon.value = o.types.length;
        }
        o.types.forEach(obj => {
            if (obj.instances.length !== 0) {
                if (obj.instances.some(item => String(item.status).toLowerCase() === 'failed')) obj.failExsit = true;
                obj.instances.forEach(ins => {
                    allInstances.push({
                        ...ins,
                        createTime: formatDate(ins.createTime)
                    });
                });
            }
        });
    });
    if (allInstances.length !== 0) {
        allInstances = [...(chunk(allInstances, 4))];
    }
    const newArr = chunk(data, 4);
    componentList.value = [...newArr];
    instanceList.value = allInstances;
    showComponent.value = true;
}
</script>
<template>
    <TopBg />
    <OdaComponent @change-list="instanceTrigger" :showComponent="showComponent" :componentList="componentList"
        :maxPolygon="maxPolygon" />
    <ComponentInstance :instanceList="instanceList" />
    <ODACanvasService />
</template>
  
<style lang="scss" scoped>
::v-deep {
    .el-carousel__arrow--left {
        left: -40px
    }

    .el-carousel__arrow--right {
        right: -40px
    }
}
</style>