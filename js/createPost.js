// Current user info
// Initialize form
document.addEventListener('DOMContentLoaded', async () => {
    // Set user info
    const currentUser = await getCurrentUser();

    document.getElementById('avatarInitials').textContent = currentUser.name.split(' ').map(n => n[0]).join('');
    document.getElementById('userName').textContent = currentUser.name;

    // Load enrolled courses

    const enrolledCourses = await getEnrolledCourses();
    const courseSelect = document.getElementById('courseSelect');

    enrolledCourses.forEach(course => {
        const option = new Option(`${course.code}: ${course.name}`, course.id);
        courseSelect.add(option);
    });
});

async function createPost() {
    const newAppointmentBody = {
        course_id: document.getElementById('courseSelect').value,
        start_time: document.getElementById('timeFrom').value,
        end_time: document.getElementById('timeTo').value,
        location: document.getElementById('location').value,
        additional_info: document.getElementById('additionalInfo').value,
    };

    const res = await createAppointment(newAppointmentBody);
    if (res.ok)
        alert("Post edited successfully!");
    else
        alert("Something went wrong.");

    // Return to feed
    window.location.href = '/html/feed.html';
}

async function editPost() {
    const newAppointmentBody = {
        course_id: document.getElementById('courseSelect').value,
        start_time: document.getElementById('timeFrom').value,
        end_time: document.getElementById('timeTo').value,
        location: document.getElementById('location').value,
        additional_info: document.getElementById('additionalInfo').value,
    };

    const res = await editAppointment(newAppointmentBody);
    if (res.ok)
        alert("Post edited successfully!");
    else
        alert("Something went wrong.");

    // Return to feed
    window.location.href = '/html/feed.html';
}