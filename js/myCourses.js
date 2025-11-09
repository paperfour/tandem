let allCourses = []





// Function to create and append course cards
async function populateCourses() {
    const coursesGrid = document.getElementById('courses-grid');
    const enrolledCourses = await getEnrolledCourses();

    if (!coursesGrid) return;
    coursesGrid.innerHTML = '';

    enrolledCourses.forEach(course => {
        const card = document.createElement('div');
        card.className = "bg-white rounded-lg shadow-md border border-gray-200 p-6 flex flex-col h-full";
        // const safeCodeId = encodeURIComponent(course.id);

        card.innerHTML = `
            <div class="flex-grow">
                <span class="text-sm font-semibold text-gray-500 uppercase">${course.code}</span>
                <h2 class="text-xl font-bold text-gray-900 mt-1 mb-3">${course.name}</h2>
            </div>
            <div class="flex gap-2">
                <a href="/html/feed.html?courseId=${course.id}" 
                    class="flex-1 text-center bg-green-800 text-white font-semibold py-2.5 px-4 rounded-lg hover:bg-green-900 transition">
                    View Feed
                </a>
                <button onclick="removeCourse('${course.code}')"
                        class="px-4 py-2.5 text-red-600 hover:bg-red-50 rounded-lg border border-red-200">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </div>
        `;

        coursesGrid.appendChild(card);
    });
}

// Function to populate available courses in modal
async function populateAvailableCourses() {
    const availableCoursesDiv = document.getElementById('availableCourses');
    const enrolledCourses = await getEnrolledCourses();
    console.log(enrolledCourses)

    availableCoursesDiv.innerHTML = allCourses.map(course => {
        const isEnrolled = enrolledCourses.some(c => c.code === course.code);
        return `
            <div class="flex items-center justify-between p-3 border rounded-lg">
                <div>
                    <div class="font-medium">${course.code}</div>
                    <div class="text-sm text-gray-500">${course.name}</div>
                </div>
                <button onclick="toggleCourse('${course.code}')"
                        class="${isEnrolled ? 'text-red-600 hover:bg-red-50' : 'text-blue-600 hover:bg-blue-50'} px-3 py-1 rounded-lg border">
                    ${isEnrolled ? 'Remove' : 'Add'}
                </button>
            </div>
        `;
    }).join('');
}

// Function to toggle course enrollment
async function toggleCourse(courseCode) {
    const enrolledCourses = await getEnrolledCourses();
    const courseIndex = enrolledCourses.findIndex(c => c.code === courseCode);
    const course = allCourses.find(c => c.code === courseCode);

    if (courseIndex > -1) {
        enrolledCourses.splice(courseIndex, 1);
    } else if (course) {
        enrolledCourses.push(course);
    }

    saveEnrolledCourses(enrolledCourses.map(t => t.id));
    await populateCourses();
    await populateAvailableCourses();
}

// Function to remove course
async function removeCourse(courseCode) {
    const enrolledCourses = await getEnrolledCourses();
    const updatedCourses = enrolledCourses.filter(c => c.code !== courseCode);
    saveEnrolledCourses(updatedCourses.map(t => t.id));
    await populateCourses();
    await populateAvailableCourses();
}

// Modal controls
document.getElementById('addCourseBtn').addEventListener('click', () => {
    document.getElementById('courseModal').classList.remove('hidden');
    populateAvailableCourses();
});

document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('courseModal').classList.add('hidden');
});

// Notifications
/* function renderNotificationsList() {
    const listEl = document.getElementById('notificationsList');
    const notifications = notificationManager.getNotifications();
    if (!listEl) return;
    if (!notifications.length) {
    listEl.innerHTML = '<p class="text-gray-500 text-center">No notifications</p>';
    return;
    }
    listEl.innerHTML = notifications.map(n => `
    <div class="mb-4 p-3 bg-gray-50 rounded-lg border ${n.status === 'pending' ? 'border-blue-200' : 'border-gray-200'}">
        <div class="flex items-center justify-between mb-2">
        <span class="font-medium text-sm text-gray-600">${n.from}</span>
        <span class="text-xs text-gray-500">${new Date(n.timestamp).toLocaleString()}</span>
        </div>
        <p class="text-sm text-gray-700">wants to join your study session for ${n.courseCode}</p>
        ${n.status === 'pending' ? `
        <div class="flex gap-2 mt-3">
            <button onclick="handleNotification(${n.id}, 'accepted')" class="px-3 py-1 text-sm text-green-600 bg-green-50 rounded-md">Accept</button>
            <button onclick="handleNotification(${n.id}, 'rejected')" class="px-3 py-1 text-sm text-red-600 bg-red-50 rounded-md">Decline</button>
        </div>` : `<div class="mt-3 text-xs text-gray-500">Status: ${n.status}</div>`}
    </div>
    `).join('');
}
function showNotifications() { document.getElementById('notificationsModal').classList.remove('hidden'); renderNotificationsList(); }
function closeNotifications() { document.getElementById('notificationsModal').classList.add('hidden'); }
function handleNotification(id, action) {
    const notifs = notificationManager.getNotifications();
    const updated = notifs.map(n => n.id === id ? {...n, status: action} : n);
    notificationManager.saveNotifications(updated);
    renderNotificationsList();
} */

// document.getElementById('notificationsBtn').addEventListener('click', () => {
//     notificationManager.updateNotificationBadge();
//     showNotifications();
// });

// document.addEventListener('DOMContentLoaded', () => notificationManager.updateNotificationBadge());

// Initialize the page
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize with some default courses if none exist
    allCourses = await (await fetchWithAuth('/all_courses', { method: 'GET' })).json();
    console.log(allCourses)
    populateCourses();
});

// Toggle avatar dropdown
const avatarBtn = document.getElementById("avatarBtn");
const dropdownMenu = document.getElementById("dropdownMenu");

avatarBtn.addEventListener("click", () => {
    dropdownMenu.classList.toggle("hidden");
});

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
    if (!avatarBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.add("hidden");
    }
});
