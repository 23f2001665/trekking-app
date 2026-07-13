// router/index.js
import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { getUserDashboard } from "@/services/getUserDashboard";

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),

    routes: [
        {
            path: "/",
            name: "Home",
            component: () => import("@/views/Home.vue"),
            meta: {
                requiresGuest: true,
            },
            children: [
                {
                    path: "login",
                    name: "Login",
                    component: () => import("@/views/auth/Login.vue"),
                    meta: {
                        requiresGuest: true,
                        requiresAuth: false,
                    },
                },
                {
                    path: "logout",
                    name: "Logout",
                    component: () => import("@/components/Logout.vue"),
                    meta: {
                        requiresAuth: true,
                        requiresGuest: false,
                    },
                },
                {
                    path: "register",
                    name: "Register",
                    component: () => import("@/views/auth/Register.vue"),
                    meta: {
                        requiresAuth: false,
                        requiresGuest: true,
                    },
                },
                {
                    path: "admin",
                    children: [
                        {
                            path: "",
                            name: "AdminDashboard",
                            component: () => import("@/views/admin/Dashboard.vue"),
                            meta: {
                                requiresAuth: true,
                                requiresGuest: false,
                            },
                        },
                    ],
                    meta: {
                        requiresAuth: true,
                        requiresGuest: false,
                    },
                },
                {
                    path: "trekker",
                    children: [
                        {
                            path: "",
                            name: "TrekkerDashboard",
                            component: () => import("@/views/trekker/Dashboard.vue"),
                            meta: {
                                requiresAuth: true,
                                requiresGuest: false,
                            },
                        },
                    ],
                    meta: {
                        requiresAuth: true,
                        requiresGuest: false,
                    },
                },
                {
                    path: "staff",
                    children: [
                        {
                            path: "",
                            name: "StaffDashboard",
                            component: () => import("@/views/staff/Dashboard.vue"),
                            meta: {
                                requiresAuth: true,
                                requiresGuest: false,
                            },
                        }
                    ],
                    meta: {
                        requiresAuth: true,
                        requiresGuest: false,
                    },
                },
                {
                    path: "error",
                    name: "403",
                    component: () => import("@/views/errors/403.vue"),
                    meta: {
                        requiresAuth: true,
                        requiresGuest: false,
                    },
                },
            ],
        }
]});

router.beforeEach(async (to) => {
    const authStore = useAuthStore();

    // Always initialize once after a fresh page load
    if (!authStore.initialized) {
        await authStore.initialize();
    }

    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        return { name: "Login" };
    }

    if (to.meta.requiresGuest && authStore.isAuthenticated) {
        return getUserDashboard(authStore.user.role);
    }

    return true;
});
export default router;