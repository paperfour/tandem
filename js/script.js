// Reload on logo click handled inline with onclick="location.reload()"

// Popup logic
const popup = document.getElementById("popup");
const closePopup = document.getElementById("close-popup");
const postBtn = document.getElementById("post-btn");
const feedBtn = document.getElementById("feed-btn");
const myCourses = document.getElementById("courses-btn")

function showPopup() {
    popup.classList.remove("hidden");
    popup.classList.add("flex");
}

function hidePopup() {
    popup.classList.add("hidden");
    popup.classList.remove("flex");
}

postBtn.addEventListener("click", showPopup);
feedBtn.addEventListener("click", showPopup);
myCourses.addEventListener("click", showPopup);
closePopup.addEventListener("click", hidePopup);
