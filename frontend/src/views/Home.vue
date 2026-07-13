<!-- views/home/Home.vue -->
<template>
    <div class="app-container">
        <header id="application-header">
            <h1 id="main-heading">🏔️ Trekking App</h1>

            <div class="user-section" v-if="isAuthenticated">
                <p class="welcome">
                    Welcome, {{ fullname }}
                </p>
                <Logout />
            </div>
        </header>

        <main class="page-container">

            <div v-if="showLandingCard" class="home-card">
                <h2>Welcome to Trekking App</h2>
                <p>Explore beautiful treks and manage your bookings with ease.</p>

                <div class="button-group">
                    <RouterLink class="btn btn-login" :to="{ name: 'Login' }">
                        Login
                    </RouterLink>

                    <RouterLink class="btn btn-register" :to="{ name: 'Register' }">
                        Register
                    </RouterLink>
                </div>
            </div>

            <RouterView />
        </main>
    </div>
</template>

<script setup>
import { computed } from "vue";
import { RouterLink, RouterView } from "vue-router";

import Logout from "@/components/Logout.vue";
import { useAuthStore } from "@/stores/auth";
import { useRoute } from "vue-router";

const authStore = useAuthStore();

const isAuthenticated = computed(() => authStore.isAuthenticated);
console.log("isAuthenticated: in Home.vue", isAuthenticated.value);

const fullname = computed(() => {
    if (!authStore.user) return "";
    return `${authStore.user.first_name} ${authStore.user.last_name}`;
});

const route = useRoute();

const showLandingCard = computed(() => {
    return !isAuthenticated.value && route.name === "Home";
});

</script>

<style scoped>
.app-container {
    min-height: 100vh;
    background: #f4f7fb;
}

/* Header */

#application-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: 1rem 2rem;

    background: white;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

#main-heading {
    margin: 0;
    font-size: 2rem;
    color: #2c3e50;
    text-transform: uppercase;
}

.user-section {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.welcome {
    margin: 0;
    font-weight: 600;
}

/* Body */

.page-container {
    min-height: calc(100vh - 80px);

    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

/* Center Card */

.home-card {
    width: 360px;

    background: white;
    border-radius: 14px;

    padding: 2rem;

    text-align: center;

    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);

    margin-bottom: 2rem;
}

.home-card h2 {
    margin-top: 0;
    color: #2c3e50;
}

.home-card p {
    color: #666;
    margin-bottom: 2rem;
}

/* Buttons */

.button-group {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

.btn {
    flex: 1;

    text-decoration: none;
    text-align: center;

    padding: 0.8rem;

    border-radius: 8px;

    font-weight: 600;

    transition: 0.2s;
}

.btn-login {
    background: #2563eb;
    color: white;
}

.btn-login:hover {
    background: #1d4ed8;
}

.btn-register {
    background: white;
    color: #2563eb;
    border: 2px solid #2563eb;
}

.btn-register:hover {
    background: #eff6ff;
}
</style>