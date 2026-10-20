
document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    const logoutButton = document.getElementById("logoutButton");

    // Mobile sidebar toggle
    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", function () {
            const isOpen = sidebar.classList.toggle("open");

            menuToggle.setAttribute(
                "aria-expanded",
                String(isOpen)
            );
        });

        // Close sidebar after selecting a navigation link
        sidebar.querySelectorAll(".nav-link").forEach(function (link) {
            link.addEventListener("click", function () {
                sidebar.classList.remove("open");

                menuToggle.setAttribute(
                    "aria-expanded",
                    "false"
                );
            });
        });
    }

    // Logout
    if (logoutButton) {
        logoutButton.addEventListener("click", async function () {
            logoutButton.disabled = true;

            try {
                // Tell the Flask backend to end the login session
                await fetch("http://127.0.0.1:5000/api/auth/logout", {
                    method: "POST",
                    credentials: "include"
                });
            } catch (error) {
                console.error("Logout request failed:", error);
            } finally {
                // Clear frontend login data
                sessionStorage.removeItem("studentData");
                sessionStorage.removeItem("isLoggedIn");

                // Choose the correct login URL for this folder
                const isPagesFolder =
                    window.location.pathname.includes("/pages/");

                window.location.href = isPagesFolder
                    ? "../login.html"
                    : "login.html";
            }
        });
    }
});
