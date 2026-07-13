// main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import { useAuthStore } from "./stores/auth";

import App from './App.vue'
import router from './router'
import {toast} from "vue-sonner";

const app = createApp(App)

const pinia = createPinia()

app.use(pinia)


app.use(router)
// const authStore = useAuthStore(pinia);
// try{
//     await authStore.initialize();
//     if (authStore.isAuthenticated) {
//         console.log("Auth store initialized");
//     } else {
//         console.log("Auth store not initialized");
//     }
// } catch (e) {
//     console.log("Auth store initialization failed:", e);
// }

app.mount('#app')

/*
const app = createApp(App);

const pinia = createPinia();

app.use(pinia);

const authStore = useAuthStore(pinia);
await authStore.initialize();

app.use(router);
app.mount("#app");
*/