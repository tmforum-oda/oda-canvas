<script setup>
import { onMounted, ref, nextTick, onBeforeUnmount, watch, defineEmits } from 'vue';
import { throttle } from 'lodash-es';
import { showLoading, hideLoading } from '@/utils/loading';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
dayjs.extend(relativeTime);
const formatDate = (timestamp, format = 'YYYY-MM-DD HH:mm:ss') => dayjs(timestamp).format(format);
const emit = defineEmits(['change-list']);
const props = defineProps({
    componentList: {
        type: Array,
        default: []
    },
    maxPolygon: {
        type: Number,
        default: 0
    },
    showComponent: {
        type: Boolean,
        default: false
    }
});

onMounted(() => {
    window.addEventListener('resize', () => {
        if (resizeFlag.value) {
            clearTimeout(resizeFlag.value);
        }
        resizeFlag.value = setTimeout(() => {
            renderHexagonalShape();
        }, 50);
    });
})

onBeforeUnmount(() => {
    window.removeEventListener('resize', renderHexagonalShape);
});

const renderHexagonalShape = async () => {
    const couple = Math.ceil(props.maxPolygon / 2);
    await nextTick();
    if (Object.prototype.toString.call(myListItem.value) !== '[object Array]' && myListItem.value?.length === 0) {
        return;
    }
    try {
        const itemWidth = Array.from(myListItem.value)[0].offsetWidth;
        const hexItemWidth = itemWidth * 0.34; // 六边形对边之和
        const hexItemPointToPointLength = hexItemWidth / 1.732 * 2; // 六边形对顶点距离
        const innerMgT = hexItemWidth / 3.464;
        const boxHeight = ((innerMgT + 4) * 3 * couple) + innerMgT;
        const maxHeight = ((hexItemPointToPointLength * 3) + innerMgT + 5);
        listHeight.value = boxHeight + 12;
        listMaxHeight.value = maxHeight;
        listPaddingTop.value = innerMgT + 5;
        polygonWidth.value = hexItemWidth;
        polygonHeight.value = hexItemPointToPointLength;
        polygonMt.value = innerMgT - (4 * 1.732);
        polygonInnerMt.value = innerMgT;
        fPolygonMl.value = (hexItemWidth + 16) / 2;
        listPaddingLeft.value = (itemWidth - ((2.5 * hexItemWidth) + 20)) / 2;
        await nextTick();
        carouselHeight.value = singleContainer.value[0].offsetHeight + 20 + 'px';
    } catch (error) { }
}

const boolFalse = ref(false);
const myListItem = ref(null);
const singleContainer = ref(null);
const carouselHeight = ref('480px');
const listHeight = ref(460);
const listMaxHeight = ref(460);
const listPaddingTop = ref(0);
const listPaddingLeft = ref(0);
const polygonWidth = ref(0);
const polygonHeight = ref(0);
const polygonMt = ref(0);
const fPolygonMl = ref(0);
const polygonInnerMt = ref(0);
const resizeFlag = ref(null);
const getPolygonStyle = idx => {
    const commonStyle = {
        width: polygonWidth.value + 'px',
        height: polygonHeight.value + 'px',
        marginTop: -polygonMt.value + 'px'
    };
    if ((idx + 1) % 4 === 3) {
        return {
            ...commonStyle,
            marginLeft: fPolygonMl.value + 'px'
        };
    }
    return commonStyle;
}
watch(() => props.componentList, () => {
    renderHexagonalShape();
});

watch(() => props.showComponent, val => {
    if (!val) {
        showLoading({ target: '.oda-components' });//打开加载中
    } else {
        hideLoading();
    }
}, { immediate: true });


const resolveInstance = throttle(async (item) => {
    const instances = item.instances || [];
    if (instances && instances.length !== 0) {
        const dealIns = instances.map(o => ({
            ...o,
            createTime: formatDate(o.createTime)
        }));
        emit('change-list', dealIns);
    } else {
        emit('change-list', []);
    }
}, 200);


</script>

<template>
    <div class="oda-components mt-5 bg-customFFF">

        <h3>{{ $t('ODA.ODA_COMPONENT') }}</h3>
        <el-carousel :height="carouselHeight" :autoplay="boolFalse" arrow="always" indicator-position="none"
            :loop="boolFalse">
            <el-carousel-item v-for="chunk in props.componentList" :key="chunk">
                <div ref="singleContainer" class="components-item bg-customBg" v-for="item in chunk" :key="item.domain">
                    <div class="instance-list-item" ref="myListItem"
                        :style="{ height: listHeight + 'px', maxHeight: listMaxHeight + 'px' }">
                        <ul :style="{ paddingTop: listPaddingTop + 'px', paddingLeft: listPaddingLeft + 'px' }">
                            <div v-for="(ins, idx) in item.types" :key="ins.type" class="polygon-six-wrap"
                                :style="getPolygonStyle(idx)">
                                <template v-if="ins?.failExsit && ins?.failExsit === true">
                                    <div class="instance-tip isntance-active-red">{{ ins?.instances.length }}</div>
                                    <div class="polygon-six isntance-active-red" @click="resolveInstance(ins)"
                                        :title="ins.type">
                                        <div class="polygon-six-inner" :style="{ marginTop: polygonInnerMt + 'px' }">
                                            {{ ins.type }}</div>
                                    </div>
                                </template>
                                <template v-else>
                                    <div class="instance-tip">{{ ins?.instances?.length }}</div>
                                    <div class="polygon-six" @click="resolveInstance(ins)" :title="ins.type">
                                        <div class="polygon-six-inner" :style="{ marginTop: polygonInnerMt + 'px' }">
                                            {{ ins.type }}</div>
                                    </div>
                                </template>

                            </div>
                        </ul>
                    </div>
                    <div class="instance-name component-list-name text-customFFF" :style="{ backgroundColor: item.color }">
                        {{ item.domain }}
                    </div>
                </div>
            </el-carousel-item>
        </el-carousel>
    </div>
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

h3 {
    padding: 10px 15px;
    color: #333;
    font-size: 16px;
}

.isntance-active-red {
    background-color: #BE3131 !important;
    color: #fff !important;
}

.polygon-six:hover {
    background-color: #e5e8eb;
}

.el-carousel__arrow--left {
    left: -40px
}

.el-carousel__arrow--right {
    right: -40px;
}

.el-carousel__item {
    width: 100%;
    height: fit-content;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 10px;
    margin-right: auto;
}

.components-item {
    color: #000;
    // border: 1px solid;
    height: fit-content;
    width: 24%;
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.13);
    border: 2px solid rgba(255, 255, 255, 1);
    position: relative;

    .component-list-name {
        position: absolute;
        bottom: 0;
        height: 35px;
        background-color: #3484f5;
        width: 100%;
        line-height: 35px;
        text-align: center;
        font-size: 15px;
        font-weight: 600;
        z-index: 10;
    }
}

.el-carousel {
    padding: 0 60px;
}

// .el-carousel__item:nth-child(2n) {
// background-color: #99a9bf;
// }

// .el-carousel__item:nth-child(2n + 1) {
// background-color: #d3dce6;
// }

.el-carousel__item:last-child {
    justify-content: left;
}

.el-carousel__item:last-child .components-item {
    margin-right: 1.5%;
}

.example-showcase .el-loading-mask {
    z-index: 9;
}

.instance-list-item {

    padding-bottom: 35px;

}

.instance-list-item ul {
    list-style: none;
    overflow-y: auto;
    overflow-x: hidden;
    width: 100%;
    padding: 0;
    height: 100%;
}

.instance-list-item ul:hover .instance-tip {
    opacity: 1;
}

.polygon-six-wrap {
    float: left;
    width: fit-content;
    height: fit-content;
    position: relative;
    margin: 0 4px;
}

.polygon-six {
    background-color: #f4f5f6;
    position: relative;
    border: 2px solid rgb(248, 245, 245);
    width: 100%;
    height: 100%;
    z-index: 7;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.13);
    transition: all 0.2s linear;
    -webkit-clip-path: polygon(50% 1%, 100% 25%, 100% 75%, 50% 99%, 0 75%, 0 25%);
    clip-path: polygon(50% 1%, 100% 25%, 100% 75%, 50% 99%, 0 75%, 0 25%);
}

.polygon-six-inner {
    width: 100%;
    height: 50%;
    overflow: hidden;
    font-weight: 650;
    text-overflow: ellipsis;
    position: absolute;
    padding: 0 10px;
    font-size: 12px !important;
    color: #4c4c4c;
}

.instance-list-item>ul .instance-tip {
    position: absolute;
    line-height: initial;
    background-color: #ECEFF4;
    border: 1px solid rgba(255, 255, 255, 1);
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.3);
    border-radius: 8.5px;
    width: 26px;
    height: 16px;
    line-height: 1;
    right: 15%;
    top: 8%;
    z-index: 666;
    text-align: center;
    color: #333;
    font-weight: 500;
    opacity: 0;
    transition: all 0.2s linear;
}
</style>
