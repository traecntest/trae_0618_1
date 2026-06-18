import { createStore } from "vuex";
import axios from "axios";

const API_BASE = "<% api_prefix %>";

export default createStore({
  state: {
    user: null,
    token: localStorage.getItem("token") || "",
  },
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      localStorage.setItem("token", token);
    },
    SET_USER(state, user) {
      state.user = user;
    },
    LOGOUT(state) {
      state.token = "";
      state.user = null;
      localStorage.removeItem("token");
    },
  },
  actions: {
    async login({ commit }, credentials) {
      const formData = new FormData();
      formData.append("username", credentials.username);
      formData.append("password", credentials.password);
      const response = await axios.post(`${API_BASE}/auth/token`, formData);
      commit("SET_TOKEN", response.data.access_token);
      return response.data;
    },
    logout({ commit }) {
      commit("LOGOUT");
    },
  },
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
});
