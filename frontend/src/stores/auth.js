// stores/auth.js

import { defineStore } from "pinia";
import api from "@/services/api";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    initialized: false,
  }),

  getters: {
    isAuthenticated: (state) => state.user !== null,
  },

  actions: {
    setUser(user) {
      this.user = user;
      this.initialized = true;
    },

    clearUser() {
      this.user = null;
      this.initialized = true;
    },

    async initialize() {
      console.log("initialize() started");

      try {
        const response = await api.get("/user_info");
        console.log("user_info:", response.data);

        this.user = response.data.user_info;
      } catch (err) {
        console.error("initialize failed:", err);
        this.user = null;
      } finally {
        this.initialized = true;
        console.log("initialize() completed");
      }
    }
  }
});