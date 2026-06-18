<template>
  <div class="form-container">
    <h2>测试表单</h2>
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="submitForm"
    >

      <el-form-item label="用户名" prop="username" required>

        <el-input
          v-model="formData.username"
          :placeholder="''"
          :type="'text'"
        />

      </el-form-item>

      <el-form-item label="年龄" prop="age" >

        <el-input
          v-model="formData.age"
          :placeholder="''"
          :type="'number'"
        />

      </el-form-item>

      <el-form-item label="邮箱" prop="email" >

        <el-input
          v-model="formData.email"
          :placeholder="''"
          :type="'text'"
        />

      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitForm">提交</el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "测试表单Form",
  data() {
    return {
      formData: {

        username: "",

        age: "",

        email: "",

      },
      rules: {


        username: [{ required: true, message: "用户名是必填项", trigger: "blur" }],






      },
    };
  },
  methods: {
    async submitForm() {
      try {
        await axios.post("/api/v1/forms/测试表单/", {
          data: this.formData,
        });
        this.$message.success("提交成功!");
        this.resetForm();
      } catch (error) {
        this.$message.error("提交失败");
      }
    },
    resetForm() {
      this.$refs.formRef.resetFields();
    },
  },
};
</script>

<style scoped>
.form-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}
</style>