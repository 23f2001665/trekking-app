<template>
    <div>
        <h1>Login</h1>
        <form @submit.prevent="login">
            <div>
                <label for="email">Email:</label>
                <input type="email" id="email" v-model="email" required />
            </div>
            <div>
                <label for="password">Password:</label>
                <input type="password" id="password" v-model="password" required />
            </div>
            <button type="submit">Login</button>
        </form>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </div>
</template>

<script>
import api from '@/services/api'; // Adjust the import path as needed
import router from '@/router/index'; // Adjust the import path as needed
import { useAuthStore } from '@/stores/auth';

export default {
    data() {
        return {
            email: '',
            password: '',
            errorMessage: ''
        }
    },
    methods: {
        async login() {
            try {
                const response = await api.post('/login', {
                    email: this.email,
                    password: this.password
                });
                // Handle successful login
                console.log(response.data);
                const authStore = useAuthStore();
                authStore.setToken(response.data); // Assuming the token is returned in response.data.token
                router.push('/dashboard'); // Redirect to dashboard or another page
            } catch (error) {
                this.errorMessage = 'Invalid email or password';
            }
            console.log("Login attempted with email:", this.email, "and password:", this.password);
        }
    }
}
</script>