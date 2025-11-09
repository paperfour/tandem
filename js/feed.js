// // User's enrolled courses (same as in main /html/courses.html)
// const enrolledCourses = [
//     { code: "CS 101", title: "Introduction to Computer Science" },
//     { code: "MATH 201", title: "Calculus II" },
//     { code: "PHYS 150", title: "General Physics" },
//     { code: "ENG 205", title: "American Literature" },
//     { code: "CHEM 301", title: "Organic Chemistry" },
//     { code: "HIST 120", title: "World History" }
// ];

let enrolledCourses = [];

// Current user info
// const currentUser = {
//     name: "Alex Thompson",
//     year: "2025",
//     major: "Computer Science" 
// };

let currentUser = null;

// Helper function to format time (e.g., 14:30 -> 2:30 PM)
// 2022-05-06 14:30
function formatTime(timeString) {
    if (!timeString) return '';
    try {
        // const [hours, minutes] = timeString.split(':');
        // const h = parseInt(hours, 10);
        // const m = parseInt(minutes, 10);
        // const ampm = h >= 12 ? 'PM' : 'AM';
        // const formattedHours = h % 12 === 0 ? 12 : h % 12;
        // const formattedMinutes = m < 10 ? '0' + m : m;
        // return `${formattedHours}:${formattedMinutes} ${ampm}`;
        return timeString.replaceAll('-', '/')
    } catch (e) {
        return "Time";
    }
}

async function drawFeed() {
    const params = new URLSearchParams(window.location.search);

    // Extract a specific parameter
    const courseId = params.get("courseId");
    console.log(params)
    console.log(courseId)
    console.log(typeof courseId)

    currentUser = await getCurrentUser();
    enrolledCourses = await getEnrolledCourses();

    const postFeedContainer = document.getElementById('all-post-container');

    // Get posts from localStorage
    const allAppointments = await getFeed();

    // Filter new posts from localStorage by enrolled courses
    let posts = await Promise.all(allAppointments
        .map(async appt => {
            // const courseCode = appt.courseName.split(':')[0].trim();
            const course = await getCourse(appt.course_id)
            const creator = await getCreator(appt.id)
            return {
                id: appt.id,
                creatorId: appt.creator_student_id,
                name: creator.name,
                courseId: course.id,
                courseName: course.name,
                courseCode: course.code,
                from: appt.start_time,
                to: appt.end_time,
                location: appt.location,
                additional_info: appt.additional_info,
                status: true
            }
        }))

    if (!courseId) {
        posts = posts
            .filter(post => enrolledCourses.some(course => course.id === post.courseId));
    } else {
        posts = posts
            .filter(post => Number(courseId) === post.courseId);
    }

    // Render filtered posts
    postFeedContainer.innerHTML = '';

    posts.reverse().forEach(post => {
        const postHTML = createPostCardHTML(post);
        postFeedContainer.insertAdjacentHTML('beforeend', postHTML);
    });

    if (posts.length === 0) {
        const noPostsHTML = `<i>No posts found for you here...</i>`
        postFeedContainer.insertAdjacentHTML('beforeend', noPostsHTML);
    }
}

// --- Main Script ---
document.addEventListener('DOMContentLoaded', drawFeed());

setInterval(drawFeed, 5000);

// This function creates the HTML for a single post card
function createPostCardHTML(post) {
    const avatarText = post.name.split(' ').map(n => n[0]).join('');
    const timeString = (post.from && post.to) ? `${formatTime(post.from)} - ${formatTime(post.to)}` : '';

    const statusColor = true;

    let joined = currentUser.appointment_id === post.id;
    let isCreator = post.creatorId === currentUser.id;

    // This is the clickable course tag
    const courseTagHTML = `
        <a href="/html/feed.html?courseId=${encodeURIComponent(post.courseId)}" 
            class="text-sm font-medium text-indigo-600 hover:underline">
            ${post.courseCode} ${post.courseName}
        </a>`;

    const studyPlanHTML = (post.goal || timeString) ? `
        <div class="bg-gray-50 border border-gray-200 p-4 rounded-lg mb-4">
            <h4 class="font-semibold text-gray-800 mb-2">Study Plan:</h4>
            ${post.goal ? `<p class="text-gray-700"><strong>Goal:</strong> ${post.goal}</p>` : ''}
            ${timeString ? `
            <p class="text-gray-700 flex items-center mt-1">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4 mr-2 text-gray-500"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> 
                ${timeString}
            </p>` : ''}
        </div>` : '';

    // Add action button (Edit for user's posts, Join for others')
    const actionButton = isCreator
        ? `<button onclick="editPost()" 
                class="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-md border border-blue-200">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Edit
            </button>
        <button onclick="endAppointment(${post.id})" 
            class="ml-2 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-md border border-red-200">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            End
        </button>`
        : `<button onclick="${!joined ? 'joinAppointment' : 'leaveAppointment'}(${post.id})" 
                class="px-4 py-2 text-sm font-medium text-${joined ? 'red' : 'green'}-600 hover:bg-${joined ? 'red' : 'green'}-50 rounded-md border border-${joined ? 'red' : 'green'}-200">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
                ${!joined ? 'Join' : 'Leave'}
            </button>`;

    // Note: data-coursecode="${post.courseCode}" is for the filter
    return `
    <div class="post-card bg-white p-6 rounded-lg shadow-lg border border-gray-200" 
            data-coursecode="${post.id}">
        
        <!-- Post Header -->
        <div class="flex items-center mb-4">
            <div class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center mr-4 border-2 border-gray-300">
                <span class="font-semibold text-gray-600">${avatarText}</span>
            </div>
            <div>
                <a href="/html/profile.html" class="text-lg font-semibold text-indigo-600 hover:underline">
                    ${post.name}
                </a>

            </div>
        </div>
        
        <!-- Course Tag -->
        <div class="mb-4">
            ${courseTagHTML}
        </div>

        <!-- Status Badge -->
        
        <!-- Study Plan Box -->
        ${studyPlanHTML}
        
        <!-- Location -->
        <div class="mb-4">
            <p class="text-gray-700 flex items-start">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5 mr-2 text-gray-500 flex-shrink-0 mt-1"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> 
                <strong>Location:</strong>&nbsp;${post.location}
            </p>
        </div>
        
        <!-- Additional Info -->
        ${post.additional_info ? `
        <div class="border-t border-gray-200 pt-4">
            <p class="text-gray-600">${post.additional_info}</p>
        </div>` : ''}

        <!-- Action Button -->
        <div class="mt-4 flex justify-end">
            ${actionButton}
        </div>
    </div>
    `;
}

// Add these functions to handle button clicks
function editPost() {
    window.location.href = `/html/editPost.html`;
}

async function joinStudySession(courseCode, ownerName) {
    // try {
    //     await notificationManager.sendJoinRequest(courseCode, ownerName, currentUser);
    //     alert('Join request sent! The study buddy will be notified.');
    // } catch (error) {
    //     console.error('Error sending join request:', error);
    //     alert('Failed to send join request. Please try again.');
    // }

}

// function renderNotificationsList() {
//     const listEl = document.getElementById('notificationsList');
//     const notifications = notificationManager.getNotifications();
//     if (!listEl) return;
//     if (!notifications.length) {
//     listEl.innerHTML = '<p class="text-gray-500 text-center">No notifications</p>';
//     return;
//     }
//     listEl.innerHTML = notifications.map(n => `
//     <div class="mb-4 p-3 bg-gray-50 rounded-lg border ${n.status === 'pending' ? 'border-blue-200' : 'border-gray-200'}">
//         <div class="flex items-center justify-between mb-2">
//         <span class="font-medium text-sm text-gray-600">${n.from}</span>
//         <span class="text-xs text-gray-500">${new Date(n.timestamp).toLocaleString()}</span>
//         </div>
//         <p class="text-sm text-gray-700">wants to join your study session for ${n.courseCode}</p>
//         ${n.status === 'pending' ? `
//         <div class="flex gap-2 mt-3">
//             <button onclick="handleNotification(${n.id}, 'accepted')" class="px-3 py-1 text-sm text-green-600 bg-green-50 rounded-md">Accept</button>
//             <button onclick="handleNotification(${n.id}, 'rejected')" class="px-3 py-1 text-sm text-red-600 bg-red-50 rounded-md">Decline</button>
//         </div>` : `<div class="mt-3 text-xs text-gray-500">Status: ${n.status}</div>`}
//     </div>
//     `).join('');
// }

// function showNotifications() {
//     document.getElementById('notificationsModal').classList.remove('hidden');
//     renderNotificationsList();
// }

// function closeNotifications() {
//     document.getElementById('notificationsModal').classList.add('hidden');
// }

// function handleNotification(id, action) {
//     const notifs = notificationManager.getNotifications();
//     const updated = notifs.map(n => n.id === id ? {...n, status: action} : n);
//     notificationManager.saveNotifications(updated);
//     renderNotificationsList();
// }

// // Notifications button wiring
// document.getElementById('notificationsBtn').addEventListener('click', () => {
//     notificationManager.updateNotificationBadge();
//     showNotifications();
// });

// --- Avatar Dropdown Script ---
const avatarBtn = document.getElementById("avatarBtn");
const dropdownMenu = document.getElementById("dropdownMenu");

if (avatarBtn) {
    avatarBtn.addEventListener("click", () => {
        dropdownMenu.classList.toggle("hidden");
    });
}
document.addEventListener("click", (e) => {
    if (dropdownMenu && !dropdownMenu.classList.contains('hidden') && avatarBtn && !avatarBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.add("hidden");
    }
});

// // update badge on load
// document.addEventListener('DOMContentLoaded', () => {
//     notificationManager.updateNotificationBadge();
// });

// temp remove
// `<span class="inline-block ${statusColor} text-sm font-medium px-3 py-1 rounded-full mb-4">
//             ${post.status}
//         </span>`