<!-- Components/Logout.vue -->
<template>
  <div>
    <button @click="logout">Logout</button>
  </div>
</template>

 <script setup>
    import api from '@/services/api'; // Adjust the import path as needed
import { useAuthStore } from '@/stores/auth';
import router from '@/router/index'; // Adjust the import path as needed
import { ref } from 'vue';
import { toast } from "vue-sonner";

const authStore = useAuthStore();
const errorMessage = ref('');

async function logout() {
    errorMessage.value = '';
    try {
        await api.post('/logout');
        authStore.clearUser();
        await router.push({ name: 'Login' });
        toast.success("Logout successful");
    } catch (error) {
        errorMessage.value = error.message;
        toast.error(error.message);
        toast.error("Logout failed");
    }
}
 </script>