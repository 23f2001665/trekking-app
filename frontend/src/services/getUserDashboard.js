// services/getUserDashboard.js
export  function getUserDashboard(role) {
    switch (role) {
        case "admin":
            return { name: "AdminDashboard" };

        case "staff":
            return { name: "StaffDashboard" };

        case "trekker":
            return { name: "TrekkerDashboard" };

        default:
            return { name: "Login" };
    }
}
