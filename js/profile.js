(async () => {

    const data = await getCurrentUser();

    let course_ids = data.courses

    for (let i of course_ids) {
        let course = await fetch(`/course/${i}`);
    }

    document.title = data.name + "'s Profile";


    const nameEl = document.querySelector('div h1');
    nameEl.innerHTML = data.name;

    const namePic = document.getElementsByClassName('avatar')[0];
    namePic.innerHTML = data.name.split(' ').map(n => n[0]).join('');

    async function populateProfileCourses() {

        const courseList = document.getElementById('profileCourseList');

        const enrolledCourses = await getEnrolledCourses();

        courseList.innerHTML = enrolledCourses.map(course =>
            `<li>${course.code}: ${course.name}</li>`
        ).join('');
    }

    await populateProfileCourses();
})()

