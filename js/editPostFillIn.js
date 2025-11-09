async function fillPost() {
    
    const currentUser = await getCurrentUser();
    let appt = await getAppointment(currentUser.appointment_id)

    document.getElementById('courseSelect').value = appt.course_id
    document.getElementById('timeFrom').value = appt.start_time
    document.getElementById('timeTo').value = appt.end_time
    document.getElementById('location').value = appt.location
    document.getElementById('additionalInfo').value = appt.additional_info
}

(async () => { await fillPost(); })()