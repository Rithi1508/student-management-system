document.addEventListener("DOMContentLoaded", function () {

    // Display the current date
    const currentDate = document.getElementById("currentDate");

    if (currentDate) {

        currentDate.textContent = new Date().toLocaleDateString(
            "en-IN",
            {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );

    }

    // Read demonstration student data
    const storedData = sessionStorage.getItem("studentData");

    let student = {
        name: "Demo Student",
        studentId: "DEMO001",
        course: "Computer Science",
        semester: "Semester 4"
    };

    if (storedData) {

        try {

            const parsedData = JSON.parse(storedData);

            student = {
                ...student,
                ...parsedData
            };

        } catch (error) {

            console.error("Unable to read student data.");

        }

    }

    // Update the welcome message
    const welcomeMessage = document.getElementById("welcomeMessage");

    if (welcomeMessage) {
        welcomeMessage.textContent =
            `Welcome back, ${student.name}!`;
    }

    // Update sidebar student name
    const sidebarStudentName =
        document.getElementById("sidebarStudentName");

    if (sidebarStudentName) {
        sidebarStudentName.textContent = student.name;
    }

    // Generate initials
    const initials = student.name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map(function (part) {
            return part.charAt(0).toUpperCase();
        })
        .join("");

    // Update avatar initials
    const sidebarAvatar = document.getElementById("sidebarAvatar");
    const topbarAvatar = document.getElementById("topbarAvatar");

    if (sidebarAvatar) {
        sidebarAvatar.textContent = initials || "S";
    }

    if (topbarAvatar) {
        topbarAvatar.textContent = initials || "S";
    }

    // Update semester display
    const semesterValue = document.getElementById("semesterValue");

    if (semesterValue) {

        const semesterNumber = student.semester.match(/\d+/);

        semesterValue.textContent = semesterNumber
            ? semesterNumber[0]
            : student.semester;

    }

});