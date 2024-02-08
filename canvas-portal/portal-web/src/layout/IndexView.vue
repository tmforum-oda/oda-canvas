<script setup>
import NavBar from '@/layout/components/NavBar.vue';
import HeaderView from '@/layout/components/Header.vue';
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import useStore from '@/stores/namespace';
const namespaceStore = useStore();
const route = useRoute();
const namespace = computed(() => namespaceStore.namespace); // namespace的获取放在顶层，获取后再进行渲染
const dataSource = computed(() => namespaceStore.dataSource); // namespace的获取放在顶层，获取后再进行渲染
const showNav = ref(false);
showNav.value = route.name !== 'ComponentDetail';
</script>
<template>
    <div class="common-layout" v-if="namespace">
        <div class="common-header">
            <HeaderView />
        </div>
        <div class="outer-container">
            <el-container style="padding: 0px 20px 20px">
                <el-aside v-if="showNav" id="sideBar" width="200px" min-height="800px">
                    <NavBar />
                </el-aside>
                <el-main>
                    <router-view></router-view>
                </el-main>
            </el-container>
        </div>
    </div>
</template>
<style lang="scss" scoped>
.common-layout {
    // padding: 0 1.5rem 1.5rem;

    .outer-container {
        margin-top: var(--height-top-bar);
        overflow-y: auto;
        height: calc(100vh - var(--height-top-bar));
        padding-top: 20px;
    }

    .common-header {
        height: 100%;
    }

    .common-header {
        position: fixed;
        z-index: 999;
        width: 100%;
        top: 0;
        height: var(--height-top-bar);
        background-color: #4051a5 !important;
    }

    .el-aside .el-menu {
        height: 100%;
    }

    .el-main {
        // background-color: #fff;
        padding: 0 0 0 10px;
    }
}

.layout-container-demo .el-header {
    position: relative;
    background-color: var(--el-color-primary-light-7);
    color: var(--el-text-color-primary);
}

.layout-container-demo .el-aside {
    color: var(--el-text-color-primary);
    background: var(--el-color-primary-light-8);
}

.layout-container-demo .el-menu {
    border-right: none;
}

.layout-container-demo .el-main {
    padding: 0;
    padding-bottom: 0;
}

.layout-container-demo .toolbar {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    right: 20px;
}
</style>