import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Home",
    component: () => import("./views/home_page.vue"),
  },
<%% for page_id, page in pages.items() %%>
  {
    path: "<% page.route %>",
    name: "<% page.name %>",
    component: () => import("./views/<% page.name.lower().replace(' ', '_') %>_page.vue"),
  },
<%% endfor %%>
<%% for form_id, form in forms.items() %%>
  {
    path: "/form/<% form.name.lower().replace(' ', '_') %>",
    name: "<% form.name %>",
    component: () => import("./views/<% form.name.lower().replace(' ', '_') %>_form.vue"),
  },
<%% endfor %%>
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
