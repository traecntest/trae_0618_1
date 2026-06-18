<template>
  <div class="page-container">
    <h2>{{ page.title || page.name }}</h2>
    <div class="page-content">
      <div v-for="component in pageComponents" :key="component.id">
        <component :is="getComponentType(component.type)" :data="component" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "<% page.name %>Page",
  data() {
    return {
      pageComponents: <% page.root_component.children | tojson %>,
    };
  },
  methods: {
    getComponentType(type) {
      return `component-${type}`;
    },
  },
};
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.page-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
