
async function getCurrentUser() {
    const res = await fetchWithAuth('/current_user', { method: 'GET' });
    const data = await res.json()
    return data;
}

// Function to get enrolled courses from db
async function getEnrolledCourses() {
    const res = await fetchWithAuth('/get_courses_for_student')
    return await res.json()
}

// Function to save enrolled courses to the db
async function saveEnrolledCourses(course_ids) {
    const res = await fetchWithAuth('/set_courses_for_student', {
        method: 'POST',
        body: JSON.stringify({ course_ids })
    })
}

async function getFeed() {
    const res = await fetchWithAuth('/feed/')
    return await res.json()
}

async function getCourse(id) {
    const res = await fetch(`/course/${id}`)
    return await res.json()
}

async function getAppointment(id) {
    const res = await fetch(`/appointment/${id}`)
    return await res.json()
}

async function getCreator(aid) {
    const res = await fetch(`/get_creator/${aid}`)
    return await res.json()
}

async function createAppointment(body) {
    const res = await fetchWithAuth('/create_appointment/', { method: 'POST', body: JSON.stringify(body) })
    return res;
}

async function editAppointment(body) {
    const res = await fetchWithAuth('/edit_appointment/', { method: 'POST', body: JSON.stringify(body) })
    return res;
}

async function joinAppointment(aid) {
    const res = await fetchWithAuth(`/join_appointment/${aid}`, { method: 'POST' })
    if (res.ok)
        alert("Study session joined!")
    else alert("Something went wrong, cannot join study session.")

    location.reload(true)
}

async function leaveAppointment() {
    const res = await fetchWithAuth(`/leave_appointment/`, { method: 'POST' })
    if (res.ok)
        alert("Study session left!")
    else alert("Something went wrong, cannot leave study session.")

    location.reload(true)
}

async function endAppointment() {
    const res = await fetchWithAuth(`/end_appointment/`, { method: 'POST' })
    if (res.ok)
        alert("Study session ended!")
    else alert("Something went wrong; cannot end study session.")

    location.reload(true)


}