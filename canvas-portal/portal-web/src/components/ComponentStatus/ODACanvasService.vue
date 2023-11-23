<script setup>

</script>
<template>
    <div class="component-instance mt-5 bg-customFFF pb-3">
        <h3> ODA Canvas Service</h3>
        <div class="oda-service flex-spa-btw">
            <div class="" style="width: 24%;">
                <div class="oda-canvas-title">
                    <div class="oda-canvas-img">
                        <div class="oda-canvas-img-wrap">
                            <div>
                                ODA Canvas</div>
                            <div class="transparent-cover"></div>
                            <div class="title-triangel">
                                <div class="title-triangel-cover"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="oda-service-item api-gateway">
                    <div class="flex-spa-btw">
                        <span class="oda-service-item-font">API Gateway</span>
                        <!-- <i class="fa fa-check-circle" style="color: #15AA41;font-size: 16px;"></i> -->
                    </div>
                    <div class="flex-spa-btw" style="margin-top: 8px;">
                        <div>
                            <img style="width: 17px;height: 11px;" src="@/assets/images/whale-icon.png" alt="">
                            <span class="component-name"></span>
                        </div>
                        <div class="service-item-readystate">

                        </div>
                    </div>
                </div>
                <div class="oda-service-item">
                    <div class="">
                        <span class="oda-service-item-font">Load Balancer</span>
                    </div>
                    <div class="mt-2">
                        <svgIcon class="inline-block" name="info" />
                        <span class="not-deployed">Not deployed</span>
                    </div>
                </div>
                <div class="oda-service-item">
                    <div class="">
                        <span class="oda-service-item-font">License Manager</span>
                    </div>
                    <div class="mt-2">
                        <svgIcon class="inline-block" name="info" />
                        <span class="not-deployed">Not deployed</span>
                    </div>
                </div>

            </div>

            <div class="mt-2" style="width: 49%;">
                <div class="rt-env">
                    <div class="rt-env-topbg">
                        Runtime Environment
                    </div>

                    <div class="k8s-status" style="padding: 80px 30px 20px;">
                        <div class="col-sm-12 k8s-status-wrapper mgt">
                            <img style="width: 18px;height: 18px;" src="@/assets/images/k8s-icon.svg" alt="">
                            <span class="k8s-status-label" style="margin: 0 5px;">Kubernetes</span>
                            <span class="k8s-status-label k8s-gitVersion" style="margin-left: 5px;"></span>
                        </div>
                    </div>
                </div>

                <div class="flex-spa-btw mt-2">
                    <div class="oda-service-item" style="margin: 0;width: 49%;">
                        <div class="flex-spa-btw">
                            <span class="oda-service-item-font">Service Mesh</span>
                            <!-- <i class="fa fa-times-circle"
                                style="color: #E45555 ;font-size: 16px;font-weight: bold;"></i> -->
                        </div>
                        <div class="mt-2">
                            <svgIcon class="inline-block" name="info" />
                            <span class="not-deployed">Not deployed</span>
                        </div>
                    </div>
                    <div class="oda-service-item" style="margin: 0;width: 49%;">
                        <div class="">
                            <span class="oda-service-item-font">Authorization</span>
                        </div>
                        <div class="mt-2">
                            <svgIcon class="inline-block" name="info" />
                            <span class="not-deployed">Not deployed</span>
                        </div>
                    </div>
                </div>
            </div>



            <div class="" style="width: 24%;">
                <div class="oda-service-item">
                    <div class="">
                        <span class="oda-service-item-font">Service Registry</span>
                    </div>
                    <div class="mt-2">
                        <svgIcon class="inline-block" name="info" />
                        <span class="not-deployed">Not deployed</span>
                    </div>
                </div>
                <div class="oda-service-item">
                    <div class="">
                        <span class="oda-service-item-font">Logging</span>
                    </div>
                    <div class="mt-2">
                        <svgIcon class="inline-block" name="info" />
                        <span class="not-deployed">Not deployed</span>
                    </div>
                </div>
                <div class="oda-service-item">
                    <div class="">
                        <span class="oda-service-item-font">Event Hub</span>
                    </div>
                    <div class="mt-2">
                        <svgIcon class="inline-block" name="info" />
                        <span class="not-deployed">Not deployed</span>
                    </div>
                </div>
                <div class="oda-service-item">
                    <div class="">
                        <span class="oda-service-item-font">Service Discovery</span>
                    </div>
                    <div class="mt-2">
                        <svgIcon class="inline-block" name="info" />
                        <span class="not-deployed">Not deployed</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.component-instance {
    .flex-spa-btw {
        display: flex;
        justify-content: space-between;
    }

    .oda-service-item-font {
        font-size: 14px;
        color: #333;
        font-weight: 500;
    }

    .not-deployed {
        color: #999;
        margin-left: 5px;
        font-size: 12px;
    }

    .oda-service {
        margin: 18px 30px;
        background-color: #EBEFF5;
        border-radius: 30px;
        padding: 20px 30px;
    }

    .oda-service-item {
        box-shadow: 0 1px 3px hsl(0deg 0% 39% / 20%);
        border-radius: 5px;
        padding: 10px 20px;
        margin: 10px 0;
        background-color: #fff;
        overflow: hidden;
        height: 70px;
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

    // background-color: #fff;
    h3 {
        padding: 10px 15px;
        color: #333;
        font-size: 16px;
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

    .rt-env {
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
}</style>