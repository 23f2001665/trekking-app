<!-- views/auth/Register.vue -->
<template>
    <div class="register-container">
        <h1>Register</h1>

        <div class="box">
            <form @submit.prevent="register">

                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" v-model="user.email" pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$" required />
                </div>

                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" v-model="user.password" required />
                </div>

                <div class="form-group">
                    <label for="first_name">First Name</label>
                    <input type="text" id="first_name" v-model="user.first_name" pattern="[a-zA-Z]{80}" required />
                </div>

                <div class="form-group">
                    <label for="last_name">Last Name</label>
                    <input type="text" id="last_name" v-model="user.last_name" pattern="[a-zA-Z]{80}" />
                </div>

                <button type="submit">
                    Register
                </button>

            </form>
            <p>Already have an account? <RouterLink :to="{ name: 'Login' }">Log in</RouterLink></p>
        </div>
    </div>
</template>

<script setup>
    import { reactive } from "vue";
    import { useRouter } from "vue-router";
    import api from "@/services/api";
    import { toast } from "vue-sonner";

    const router = useRouter();

    const user = reactive({
        email: "",
        password: "",
        first_name: "",
        last_name: "",
    });

    async function register() {
        try {
            await api.post("/register", {
                email: user.email,
                password: user.password,
                first_name: user.first_name,
                last_name: user.last_name,
            });

            toast.success("Registration successful. Please log in.");

            await router.push({ name: "Login" });

        } catch (err) {
            toast.error(err.response?.data?.message || "Registration failed");
        }
    }
</script>

<style scoped>
    .register-container {
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    h1 {
        margin-bottom: 2rem;
        color: #2c3e50;
    }

    .box {
        width: 100%;
        max-width: 420px;

        background: white;

        padding: 2rem;

        border-radius: 12px;

        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    }

    .form-group {
        display: flex;
        flex-direction: column;

        margin-bottom: 1.2rem;
    }

    label {
        margin-bottom: 0.5rem;
        font-weight: 600;
        color: #444;
    }

    input {
        padding: 0.8rem;

        border: 1px solid #ccc;
        border-radius: 8px;

        font-size: 1rem;
    }

    input:focus {
        outline: none;
        border-color: #2563eb;
    }

    button {
        width: 100%;

        padding: 0.9rem;

        border: none;
        border-radius: 8px;

        background: #2563eb;
        color: white;

        font-size: 1rem;
        font-weight: 600;

        cursor: pointer;

        transition: background 0.2s;
    }

    button:hover {
        background: #1d4ed8;
    }
</style>