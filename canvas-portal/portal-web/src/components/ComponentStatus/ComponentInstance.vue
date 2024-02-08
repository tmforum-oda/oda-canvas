<script setup>
import { ref } from 'vue';
const boolFalse = ref(false);
const props = defineProps({
    instanceList: {
        type: Array,
        default: []
    },
})
const viewDetail = (name) => {
    const url = '#/ComponentDetail/' + name;
    window.open(url);
}

</script>
<template>
    <div class="component-instance mt-5 pb-5 bg-customFFF">
        <h3>
            {{ $t('ODA.COMPONENT_INSTANCES') }}
        </h3>
        <el-carousel v-if="instanceList.length !== 0" height="370px" :autoplay="boolFalse" arrow="always"
            indicator-position="none" :loop="boolFalse">
            <el-carousel-item v-for="(o, idx) in props.instanceList" :key="idx">

                <div class="instance-detail-item" v-for="(item, index) in o" :key="index">
                    <img class="instance-detail-item-bg" src="@/assets/images/green-bg.png">
                    <div style="height: 50%;">
                        <div class="instance-version">
                            <div class="wd-hgt-fifty-six" style="margin-right: 12px;">
                                <img src="@/assets/images/green.png" class="wd-hgt-fifty-six">
                            </div>
                            <div class="detail-instance-ver">
                                V{{ item.version }}</div>
                        </div>
                        <div class="instance-name" @click="viewDetail(item.name)">{{ item.name }}</div>
                    </div>
                    <div style="height: 50%;">
                        <div class="instance-type">
                            <div class="instance-label">Type:</div>
                            <div class="instance-label-text" title="{{ item.type }}">{{ item.type }}</div>
                        </div>
                        <div class="instance-domain">
                            <div class="instance-label">Domain:</div>
                            <div class="instance-label-text" title="{{ item.domain }}">{{ item.domain }}</div>

                        </div>
                        <div class="instance-creaete-time">
                            <div class="instance-label">Create Time:</div>
                            <div class="instance-label-text" title="{{ item.createTime }}">{{ item.createTime }}</div>
                        </div>
                        <div class="instance-status">
                            <div class="instance-label">Status:</div>
                            <div style="display:flex;align-items: center;">
                                <div class="instance-status-icon"></div>
                                <div class="instance-label-text" title="{{ item.status }}">{{ item.status }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </el-carousel-item>
        </el-carousel>
        <div v-else style="color: #909399;text-align:center">
            No data
        </div>
    </div>
</template>

<style lang="scss" scoped>
.el-carousel {
    padding: 0 60px;
}

.el-carousel__item {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 10px;
    margin-right: auto;
}

.el-carousel__item:last-child {
    justify-content: left;
}

.el-carousel__item:last-child .instance-detail-item {
    margin-right: 1.5%;
}

.component-instance {

    // background-color: #fff;
    h3 {
        padding: 10px 15px;
        color: #333;
        font-size: 16px;
    }
}


.status-view-wrap {
    font-family: PingFangSC-Medium;
}

.status-view-wrap .view-title {
    color: #333;
    font-size: 16px;
    margin-top: 0;
    font-weight: 500;
}



.status-view-wrap .top-gb-title {
    font-family: FZLTCHJW--GB1-0;
    font-size: 44px;
    color: #FFFFFF;
    font-weight: bold;
    background-image: -webkit-linear-gradient(#fff, #fff, #4A70CB);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

.status-view-wrap .top-gb-parg {
    font-size: 16px;
    color: #CDD8F1;
    font-weight: 400;
}

.status-view-wrap>.top-gb {
    width: 100%;
    height: 230px;
    padding: 40px 80px;
    background-image: url('../image/oda-background.png');
    background-size: cover;
    background-repeat: no-repeat;
}

.status-view-wrap .mgt {
    margin-top: 15px;
}

.api-monitor-list-wrap {
    flex-wrap: wrap;
    margin-top: 15px;
    display: flex;
    justify-content: space-between;
    align-items: left;
}

.api-monitor-list .api-monitor-item {
    box-shadow: 0 1px 3px hsl(0deg 0% 39% / 20%);
    border-radius: 5px;
    padding: 20px;
    transition: all 0.3s linear;
    margin: 10px 0;
    width: 23%;
    overflow: hidden;
}

.api-monitor-list .api-monitor-item:hover {
    box-shadow: 0 1px 12px hsl(0deg 1% 24% / 20%);
    transform: translateY(-4px);
}

.api-monitor-item>div {
    margin-bottom: 8px;
}

.api-monitor-item .api-desc {
    font-size: 14px;
    color: #333;
    font-weight: 500;
}

.slick-next,
.slick-prev {
    width: 32px;
    height: 32px;
    background-image: linear-gradient(180deg, #FFFFFF 1%, #F5F9FF 100%);
    border: 2px solid rgba(255, 255, 255, 1);
    border-radius: 50%;
    margin: auto 0;
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.23);
    color: #333;
    font-size: 13px;
}

.slick-next:hover,
.slick-prev:hover {
    color: #3D7FFF
}

.instance-list-wrap {
    padding: 0 42px;
}

.instance-list-wrap .instance-list-item {
    height: 324px;
    margin: 8px;
    box-shadow: 0 1px 3px hsl(0deg 0% 39% / 20%);
    border-radius: 5px;
    padding: 10px 0 32px;
    overflow: hidden;
    position: relative;
    background-image: linear-gradient(180deg, #FFFFFF 1%, #FEF5F5 100%);
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.13);

    border: 2px solid rgba(255, 255, 255, 1);

}

.item-indicator-success {
    width: 20%;
    min-width: 52px;
    background-color: #33CD60;
    text-align: right;
    height: 20px;
    line-height: 18px;
    text-align: center;
    flex-shrink: 0;

}

.item-indicator-Failing {
    width: 20%;
    min-width: 52px;
    background-color: #BE3131;
    text-align: right;
    height: 20px;
    line-height: 18px;
    text-align: center;
    flex-shrink: 0;

}

.monitor-item-indicator {
    color: #fff;
    width: 100%;
    height: 20px;
    display: flex;
}

.monitor-item-indicator>div:first-child {
    flex-grow: 1;
}

.instance-list-wrap .instance-list-item ul {
    list-style: none;
    overflow-y: auto;
    overflow-x: hidden;
    width: 100%;
    padding: 0;
    height: 100%;
}

.instance-list-wrap .instance-list-item ul:hover .instance-tip {
    opacity: 1;
}

.instance-detail-item {
    width: 24%;
    height: 100%;
    margin: 8px;
    box-shadow: 0 1px 3px hsl(0deg 0% 39% / 20%);
    border-radius: 5px;
    padding: 15px 20px;
    overflow: hidden;
    position: relative;
    background: linear-gradient(180deg, #FFFFFF 1%, #F5F9FF 100%);
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.13);
    border: 2px solid rgba(255, 255, 255, 1);
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.13);
    display: flex;
    flex-direction: column;
}

.instance-detail-item .instance-version {
    display: flex;
    justify-content: left;
    align-items: center;
}

.instance-detail-item .instance-name {
    display: inline-block;
    font-family: PingFangSC-Semibold;
    font-size: 15px;
    color: #333;
    line-height: 25px;
    font-weight: bold;
    margin: 15px 0;
}

.instance-detail-item .instance-name:hover {
    color: #3D7FFF;
    text-decoration: underline;
    cursor: pointer;
}

.instance-detail-item .instance-detail-item-bg {
    position: absolute;
    right: 0;
    bottom: 0;
    width: 40%;
}

.wd-hgt-fifty-six {
    width: 56px;
    height: 56px
}

.instance-detail-item .detail-instance-ver {
    width: 62px;
    height: 24px;
    background-image: linear-gradient(180deg, #FFFFFF 1%, #F5F9FF 100%);
    border: 2px solid rgba(255, 255, 255, 1);
    box-shadow: 0px 2px 9px 0px rgba(41, 69, 107, 0.13);
    border-radius: 4px;
    text-align: center;
    color: #333;
    font-weight: bold;
}

.instance-detail-item .instance-status-icon {
    width: 8px;
    height: 8px;
    background: #2EABA1;
    box-shadow: 0 0 2px 4px rgba(46, 171, 161, 0.24);
    border-radius: 50%;
    margin-right: 8px;
    background-color: #2eaba1
}

.instance-detail-item .instance-type,
.instance-detail-item .instance-domain,
.instance-detail-item .instance-creaete-time,
.instance-detail-item .instance-status {
    margin: 8px 0;
    display: flex;
}

.instance-detail-item .instance-label-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #646464;
}

.instance-list-wrap .instance-name {
    position: absolute;
    width: 100%;
    bottom: 0;
    left: 0;
    right: 0;
    text-align: center;
    line-height: 32px;
    height: 32px;
    font-size: 14px;
    color: #fff;
    font-weight: 600;
    box-shadow: 0px -4px 10px 0px rgba(0, 0, 0, 0.12);
    z-index: 999;
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

.status-view-wrap .oda-service-wrap .oda-service {
    margin: 18px 30px;
    background-color: #EBEFF5;
    border-radius: 30px;
    padding: 20px 30px;
}

.status-view-wrap .oda-service-wrap .oda-service-item {
    box-shadow: 0 1px 3px hsl(0deg 0% 39% / 20%);
    border-radius: 5px;
    padding: 10px 20px;
    margin: 10px 0;
    background-color: #fff;
    overflow: hidden;
    height: 70px;
}

.oda-canvas-title {
    margin: 10px 0;
    height: 70px;
    position: relative;
}

.oda-canvas-img {
    position: absolute;
    top: 0;
    left: -45px;
    width: 100%;
    background-color: #fff;
    box-shadow: 0px 2px 5px 0px rgba(8, 38, 168, 0.15);
    border-top-right-radius: 10px;
    padding: 3px;
}

.oda-canvas-img-wrap {
    background-image: linear-gradient(241deg, #1158EC 0%, #195DFF 100%);
    border-top-right-radius: 10px;
    position: relative;
}

.transparent-cover {
    position: absolute;
    width: 20px;
    height: 15px;
    bottom: -15px;
    left: -10px;
    z-index: 9;
    background-color: #fff;
}

.title-triangel::after {
    content: '';
    position: absolute;
    left: 0px;
    bottom: -20px;
    width: 0;
    height: 0;
    border-style: solid;
    border-width: 10px;
    border-color: #282797 #282797 transparent transparent;
    box-shadow: 3px -3px 3px rgba(8, 38, 168, 0.15);
    z-index: 99;
}

.transparent-cover::after {
    content: '';
    position: absolute;
    left: 6px;
    bottom: -11px;
    width: 0;
    height: 0;
    border-style: solid;
    border-width: 13px;
    border-color: #fff #fff transparent transparent;
    box-shadow: 3px -3px 3px rgba(8, 38, 168, 0.15);
    z-index: 99;
}

.flex-spa-btw {
    display: flex;
    justify-content: space-between;
}

.oda-service-item-font {
    font-size: 14px;
    color: #333;
    font-weight: 500;
}

.notdeployed-text-tip {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    display: inline-block;
    background-color: #B0B5BC;
    color: #fff;
    text-align: center;
    line-height: 14px;
}

.status-view-wrap .rt-env {
    height: 230px;
    background-color: #fff;
    border-radius: 8px;
    position: relative;
    overflow: hidden;
    background-image: url('../image/dash-bg.png');
    background-size: 30%;
    background-repeat: no-repeat;
    background-position: right bottom;
}

.rt-env-topbg {
    position: absolute;
    height: 55px;
    background-image: linear-gradient(241deg, #1158EC 0%, #195DFF 100%);
    box-shadow: 0px 2px 5px 0px;
    font-size: 16px;
    color: #fff;
    line-height: 55px;
    padding-left: 30px;
    width: 100%;
}

.instance-detail-wrap {
    padding: 0 42px;
    margin-top: 15px;
}

.instance-label {
    font-family: PingFangSC-Regular;
    font-size: 12px;
    color: #9399A3;
    font-weight: 400;
    margin-right: 13px;
    text-overflow: ellipsis;
    white-space: nowrap;
}


.k8s-status-wrapper {
    display: flex;
    align-items: center;
    justify-content: left;
}

.k8s-status-label {
    font-family: PingFangSC-Regular;
    font-size: 12px;
    color: #333;
    letter-spacing: 0.14px;
}

.k8s-true-state {
    color: #15AA41;
    margin-right: 8px;
    font-size: 16px;
}

.k8s-false-state {
    color: #E45555;
    margin-right: 8px;
    font-size: 16px;
}

.service-item-readystate {
    display: flex;
    align-items: center;
    justify-content: right;
}

.isntance-active-red {
    background-color: #BE3131 !important;
    color: #fff !important;
}

.oda-event {
    max-height: 442px;
    overflow: auto;
}

.oda-event-wrap {
    margin-top: 30px;
}

.oda-event-item {
    border-bottom: 1px solid #eee;
    margin: 30px 28px 0 28px;
}

.monitor-item-indicator-red {
    background-color: #BE3131;
    width: 5px;
    margin-right: 1px;
    flex-shrink: 0
}

.monitor-item-indicator-green {
    background-color: #33CD60;
    width: 5px;
    margin-right: 1px;
    flex-shrink: 0
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

.oda-canvas-img-wrap>div:first-child {
    font-size: 26px;
    color: #fff;
    font-weight: 500;
    text-align: center;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
    padding: 2px 0;
    height: 43px;
}

.oda-service-item .component-name {
    color: #3D7FFF;
    margin-left: 5px;
}

.api-monitor-item-label {
    color: #999;
    padding-left: 0 !important
}

.api-monitor-item-label .col-sm-6 {
    padding-left: 0 !important;
}
</style>