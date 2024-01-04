<script setup>
import { ref, onMounted, } from 'vue';
import { useRoute } from 'vue-router';
const route = useRoute();
const activeName = ref('');
onMounted(() => {
  activeName.value = route.name;
})
const handleOpen = (key, keyPath) => {
  // console.log(key, keyPath)
}
const handleClose = (key, keyPath) => {
  // console.log(key, keyPath)
}
</script>
<template>
  <el-menu mode="vertical" :default-active="activeName" active-text-color="#526ecc" class="el-menu-vertical-demo" router
    @open="handleOpen" @close="handleClose">
    <el-menu-item route="/componentStatus" index="componentStatus">
      <!-- <el-icon><icon-menu /></el-icon> -->
      <span>{{ $t('ODA.ODA_STATUS') }}</span>
    </el-menu-item>
    <el-menu-item route="/componentMap" index="ComponentMap">
      <!-- <el-icon><icon-menu /></el-icon> -->
      <span>{{ $t('ODA.ODA_MAP') }}</span>
    </el-menu-item>
    <el-menu-item route="/componentInstance" index="ComponentInstance">
      <span>{{ $t('ODA.COMPONENT_INSTANCES') }}</span>
    </el-menu-item>
    <el-menu-item route="/componentComplianceTest" index="ComponentComplianceTest">
      <span>{{ $t('ODA.COMPLIANCE_TEST') }}</span>
    </el-menu-item>
    <el-menu-item route="/componentOrchestration" index="ComponentOrchestration">
      <span>{{ $t('ODA.ORCHESTRATION') }}</span>
    </el-menu-item>
  </el-menu>
</template>
