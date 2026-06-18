<template>
  <div id="app">
    <el-container>
      <el-header v-if="showHeader">
        <h1>{{ appName }}</h1>
      </el-header>
      <el-container>
        <el-aside width="200px" v-if="showSidebar">
          <el-menu
            :default-active="activeMenu"
            router
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
          >
            <el-menu-item
              v-for="menu in menus"
              :key="menu.path"
              :index="menu.path"
            >
              {{ menu.name }}
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
export default {
  name: "App",
  data() {
    return {
      appName: "<% app_name %>",
      showHeader: true,
      showSidebar: true,
      menus: <% menus | tojson %>,
    };
  },
  computed: {
    activeMenu() {
      return this.$route.path;
    },
  },
};
</script>

<style>
#app {
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  height: 100vh;
}
</style>
