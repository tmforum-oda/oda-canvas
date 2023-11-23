<template>
    <div class="login-container">
        <div class="text-center m-auto" style="font-size: 30px;">Canvas Portal</div>
        <div class="login-card">
            <div class="login-title">管理员登录</div>
            <el-form status-icon :model="loginForm" :rules="rules" ref="form" class="login-form">
                <el-form-item prop="username">
                    <el-input size="large" :prefix-icon="User" v-model="loginForm.username" placeholder="用户名" />
                </el-form-item>
                <el-form-item prop="password">
                    <el-input size="large" :prefix-icon="Lock" v-model="loginForm.password" show-password
                        placeholder="密码" />
                </el-form-item>
            </el-form>
            <el-button type="primary" @click="login">登录</el-button>
        </div>
    </div>
</template>
  
<script setup>
// import { generaMenu } from '@/assets/js/menu'
import { ref } from "vue";
import { Lock, User } from '@element-plus/icons-vue';
import { useRouter } from "vue-router";
const router = useRouter();
const loginForm = ref({
    username: '',
    password: ''
});
const rules = {
    username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
    password: [{ required: true, message: '密码不能为空', trigger: 'blur' }]
};
const form = ref(null);
const login = () => {
    const { username, password } = loginForm.value;
    // 触发表单校验
    validateForm().then(() => {
        // 校验通过，执行登录操作
        console.log('用户名：', username);
        console.log('密码：', password);
        router.push('/componentStatus');

    }).catch(() => {
        // 校验不通过
        ElMessage.error('请填写完整登录信息');
        console.log('error');
    });
};
const validateForm = () => {
    return new Promise((resolve, reject) => {
        // 调用Element Plus的表单校验方法
        form.value.validate((valid) => {
            if (valid) {
                resolve();
            } else {
                reject();
            }
        });
    });
};
// export default {
//     data: function () {
//         return {
//             loginForm: {
//                 username: '',
//                 password: ''
//             },
//             rules: {
//                 username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
//                 password: [{ required: true, message: '密码不能为空', trigger: 'blur' }]
//             }
//         }
//     },
//     methods: {
//         login() {
//             this.$refs.ruleForm.validate((valid) => {
//                 if (valid) {
//                     const that = this
//                     let param = new URLSearchParams()
//                     param.append('username', that.loginForm.username)
//                     param.append('password', that.loginForm.password)
//                     that.axios.post('/api/users/login', param).then(({ data }) => {
//                         if (data.flag) {
//                             that.$store.commit('login', data.data)
//                             // generaMenu()
//                             that.$message.success('登录成功')
//                             that.$router.push({ path: '/' })
//                         } else {
//                             that.$message.error(data.message)
//                         }
//                     })
//                 } else {
//                     return false
//                 }
//             })
//         }
//     }
// }
</script>
<style scoped>
.login-container {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    left: 0;
    /* background: url(https://static.linhaojun.top/aurora/photos/765664a8a75211296a9cd89671d6d660.png) center center / cover no-repeat; */
    background: linear-gradient(to right, #1e5799 0%, #2989d8 30%, #207cca 63%, #7db9e8 100%);
}

.login-card {
    position: absolute;
    top: 0;
    bottom: 0;
    right: 0;
    background: #fff;
    padding: 170px 60px 180px;
    width: 350px;
}

.login-title {
    color: #303133;
    font-weight: bold;
    font-size: 1rem;
}

.login-form {
    margin-top: 1.2rem;
}

.login-card button {
    margin-top: 1rem;
    width: 100%;
}
</style>