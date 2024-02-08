<script setup>
import { ArrowDown, User, SwitchButton, Switch } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { computed, ref, watch } from 'vue';
import useStore from '@/stores/namespace';
import request from "@/utils/index";
import { useI18n } from 'vue-i18n';
import { setLanguage } from '@/utils/cookies';
const namespaceStore = useStore();
const namespace = computed(() => namespaceStore.namespace);
const namespaceVal = ref('');
watch(() => namespace, val => {
    namespaceVal.value = val.value;
}, {
    immediate: true
});

const dataSource = computed(() => namespaceStore.dataSource);

//  const dataSource = ['default','components'];
const { locale: currentLocale, t } = useI18n();
const logOut = () => {
    ElMessageBox.confirm(
        t('ODA.CONFIRM_LOGOUT'),
        'Warning',
        {
            confirmButtonText: t('ODA.OK'),
            cancelButtonText: t('ODA.CANCEL'),
            type: 'warning',
        }
    ).then(() => {
        try {
            request.logOut().then(() => {
                ElMessage({
                    type: 'success',
                    message: t('ODA.LOGOUT_SUCCESS')
                });
                window.open('login.html', '_self');
            }).catch(() => {
                window.open('login.html', '_self');
            });
        } catch (error) {

        }

    })
}
const switchI18n = () => {
    if (currentLocale.value === 'en') {
        currentLocale.value = 'zh';
        setLanguage('zh');
    } else {
        currentLocale.value = 'en';
        setLanguage('en');
    }

}
const handleCommand = (command) => {
    switch (command) {
        case 'logOut':
            logOut();
            break;
        case 'switchI18n':
            switchI18n();
            break;
        default:
            break;
    }
}
const changeNameSpace = (namespace) => {
    namespaceStore.change(namespace)
}
</script>
<template>
    <div class="flex justify-between items-center common-top">
        <div class="common-title">Canvas Portal</div>
        <div class="ml-8 flex-1 flex" style="font-size: 14px;color: #f1dfdf;">
            <div>{{ $t('ODA.NAMESPACE') }}：</div>
            <div> <el-select v-model="namespaceVal" @change="changeNameSpace" placeholder="Select" style="width: 240px">
                    <el-option v-for="item in dataSource" :key="item" :label="item" :value="item" />
                </el-select></div>
        </div>
        <div class="menu-list flex">
            <el-dropdown popper-class="common-dropdown" @command="handleCommand" placement="bottom-end" trigger="click">
                <span class="common-dropdown-link">
                    <el-icon :size="20" color="#fff">
                        <User />
                    </el-icon>
                    <el-icon :size="20" class="el-icon--right"><arrow-down /></el-icon>
                </span>
                <template #dropdown>
                    <el-dropdown-menu :style="{ width: '150px', paddingBottom: '20px' }">
                        <el-dropdown-item command="logOut">
                            <div class="flex items-center log-out-item">
                                <el-icon :size="16">
                                    <SwitchButton />
                                </el-icon>
                                <span>{{ $t('ODA.LOGOUT') }}</span>
                            </div>
                        </el-dropdown-item>
                        <el-dropdown-item command="switchI18n">
                            <div class="flex items-center log-out-item">
                                <el-icon :size="16">
                                    <Switch />
                                </el-icon>
                                <span>{{ $t('ODA.SWITCH_LAN') }}</span>
                            </div>
                        </el-dropdown-item>
                    </el-dropdown-menu>
                </template>
            </el-dropdown>
        </div>
    </div>
</template>
<style lang="scss">
.common-top {
    height: 100%;
    padding: 0 15px;
}

.common-title {
    background-color: #0c0724;
    font-size: 20px;
    // color: #646464;
    font-family: FZLTCHJW--GB1-0;
    font-size: 22px;
    color: #FFFFFF;
    // font-weight: bold;
    background-image: -webkit-linear-gradient(#fff, #fff, #4A70CB);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.menu-list {
    height: 100%;
    padding: 0 .5rem;
}

.menu-list:hover {
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}

.common-dropdown {
    overflow: hidden;
}

.common-dropdown-link {
    cursor: pointer;
    color: var(--el-color-primary);
    display: flex;
    align-items: center;
    outline: none;
}

.common-dropdown .el-dropdown-menu__item {
    font-size: 14px;
}

.log-out-item {
    padding: 5px 10px;
}
</style>