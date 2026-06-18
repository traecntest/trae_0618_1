<template>
  <div class="form-container">
    <h2><% form.name %></h2>
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="submitForm"
    >
<%% for field in form.fields %%>
      <el-form-item label="<% field.label %>" prop="<% field.name %>" <%% if field.required %%>required<%% endif %%>>
<%% if field.field_type == 'text' or field.field_type == 'number' %%>
        <el-input
          v-model="formData.<% field.name %>"
          :placeholder="'<% field.placeholder %>'"
          :type="'<% field.field_type %>'"
        />
<%% elif field.field_type == 'textarea' %%>
        <el-input
          v-model="formData.<% field.name %>"
          type="textarea"
          :rows="3"
          :placeholder="'<% field.placeholder %>'"
        />
<%% elif field.field_type == 'select' %%>
        <el-select v-model="formData.<% field.name %>" placeholder="<% field.placeholder %>">
          <el-option
            v-for="opt in <% field.options %>"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
<%% elif field.field_type == 'checkbox' %%>
        <el-checkbox v-model="formData.<% field.name %>"><% field.label %></el-checkbox>
<%% elif field.field_type == 'radio' %%>
        <el-radio-group v-model="formData.<% field.name %>">
          <el-radio
            v-for="opt in <% field.options %>"
            :key="opt.value"
            :label="opt.value"
          ><% opt.label %></el-radio>
        </el-radio-group>
<%% elif field.field_type == 'date' %%>
        <el-date-picker
          v-model="formData.<% field.name %>"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
        />
<%% elif field.field_type == 'datetime' %%>
        <el-date-picker
          v-model="formData.<% field.name %>"
          type="datetime"
          placeholder="选择日期时间"
          value-format="YYYY-MM-DD HH:mm:ss"
        />
<%% elif field.field_type == 'file' %%>
        <el-upload
          v-model="formData.<% field.name %>"
          action="#"
          :auto-upload="false"
        >
          <el-button>点击上传</el-button>
        </el-upload>
<%% else %%>
        <el-input v-model="formData.<% field.name %>" />
<%% endif %%>
      </el-form-item>
<%% endfor %%>
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
  name: "<% form.name %>Form",
  data() {
    return {
      formData: {
<%% for field in form.fields %%>
        <% field.name %>: <%% if field.default_value is not none %%><% field.default_value %><%% else %%><%% if field.field_type == 'checkbox' %%>false<%% else %%>""<%% endif %%><%% endif %%>,
<%% endfor %%>
      },
      rules: {
<%% for field in form.fields %%>
<%% if field.required %%>
        <% field.name %>: [{ required: true, message: "<% field.label %>是必填项", trigger: "blur" }],
<%% endif %%>
<%% endfor %%>
      },
    };
  },
  methods: {
    async submitForm() {
      try {
        await axios.post("/api/v1/forms/<% form.name.lower().replace(' ', '_') %>/", {
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
