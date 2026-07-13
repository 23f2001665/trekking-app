<!-- Login.vue -->
<template>
    <div>
        <h1>Login</h1>
        <div class="box">
            <form @submit.prevent="login">
                <div>
                    <label for="email">Email:</label>
                    <input type="email" id="email" v-model="user.email" required />
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" v-model="user.password" required />
                </div>
                <button type="submit">Login</button>
            </form>
            <p>Don't have an account? <RouterLink :to="{ name: 'Register' }">Register</RouterLink></p>
        </div>
    </div>
</template>


<script setup>
    import { ref, reactive } from "vue";
    import { useRouter } from "vue-router";
    import api from "@/services/api";
    import { useAuthStore } from "@/stores/auth";
    import { toast } from "vue-sonner";
    import { getUserDashboard } from "@/services/getUserDashboard";

    const router = useRouter();
    const authStore = useAuthStore();

    const user = reactive({
        email: "",
        password: "",
    });

    const errorMessage = ref("");

    async function login() {
        errorMessage.value = "";

        try {
            const response = await api.post("/login", {
                email: user.email,
                password: user.password,
            });

            const { user_info } = response.data;


            authStore.setUser(user_info);
            console.log("After setUser:", authStore.user);
            const target = getUserDashboard(user_info.role);
            console.log("Navigating to:", target);

            try {
                await router.push(target);
                console.log("Current route:", router.currentRoute.value.fullPath);
            } catch (e) {
                console.error(e);
            }
            toast.success("Login successful");

        } catch (err) {
            errorMessage.value = err.message;

        }
    }
</script>

<style scoped>
    h1 {
        text-align: center;
        margin: 2rem 0;
        color: #333;
    }

    .box {
        max-width: 360px;
        margin: 0 auto;
        padding: 2rem;
        border: 1px solid #ddd;
        border-radius: 10px;
        background: #fff;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    form {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    form div {
        display: flex;
        flex-direction: column;
    }

    label {
        margin-bottom: 0.35rem;
        font-weight: 600;
        color: #444;
    }

    input {
        padding: 0.75rem;
        font-size: 1rem;
        border: 1px solid #bbb;
        border-radius: 6px;
        outline: none;
        transition: border-color 0.2s ease;
    }

    input:focus {
        border-color: #2563eb;
    }

    button {
        margin-top: 0.5rem;
        padding: 0.75rem;
        font-size: 1rem;
        font-weight: 600;
        color: white;
        background: #2563eb;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }

    button:hover {
        background: #1d4ed8;
    }

    button:disabled {
        background: #94a3b8;
        cursor: not-allowed;
    }
</style>