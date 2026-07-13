// services/api.js
import axios from "axios";
import { useAuthStore } from "@/stores/auth";

const api = axios.create({
    baseURL: "http://localhost:5000",
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.response.use(
    response => response,

    error => {
        // Network error
        if (!error.response) {
            return Promise.reject({
                status: 0,
                message: "Unable to connect to the server.",
            });
        }

        const { status, data } = error.response;

        // Keep the auth store in sync.
        if (status === 401) {
            const authStore = useAuthStore();
            authStore.clearUser();
        }

        return Promise.reject({
            status,
            message:
                data.error ??
                data.message ??
                `Request failed (${status})`,
        });
    }
);

export default api;