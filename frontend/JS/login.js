document.addEventListener("DOMContentLoaded", function () {

    const loginForm = document.getElementById("loginForm");
    const studentId = document.getElementById("studentId");
    const password = document.getElementById("password");
    const togglePassword = document.getElementById("togglePassword");
    const loginMessage = document.getElementById("loginMessage");

    // Show or hide the password
    togglePassword.addEventListener("click", function () {

        if (password.type === "password") {
            password.type = "text";
            togglePassword.textContent = "Hide";
        } else {
            password.type = "password";
            togglePassword.textContent = "Show";
        }

    });

    // Frontend demonstration login
    loginForm.addEventListener("submit", function (event) {

        event.preventDefault();

        const enteredId = studentId.value.trim();
        const enteredPassword = password.value;

        if (!enteredId || !enteredPassword) {

            loginMessage.textContent =
                "Please enter your student ID/email and password.";

            loginMessage.style.color = "#dc2626";

            return;
        }

        // Demo data only. This is not authentication.
        const demoStudent = {
            name: "Demo Student",
            studentId: enteredId,
            course: "Computer Science",
            semester: "Semester 4"
        };

        sessionStorage.setItem(
            "studentData",
            JSON.stringify(demoStudent)
        );

        sessionStorage.setItem("isLoggedIn", "true");

        window.location.href = "dashboard.html";

    });

});