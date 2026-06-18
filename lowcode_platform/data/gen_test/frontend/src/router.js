import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Home",
    component: () => import("./views/home_page.vue"),
  },


  {
    path: "/form/测试表单",
    name: "测试表单",
    component: () => import("./views/测试表单_form.vue"),
  },

];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;