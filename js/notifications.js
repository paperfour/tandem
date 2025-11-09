// Notification management
class NotificationManager {
	// Keeps notifications in localStorage for now; replace get/save with API calls to connect backend
	constructor() {
		this.key = 'notifications';
		this.notifications = this.getNotifications();
		this.updateNotificationBadge();
		// optional: poll or connect WebSocket here
	}

	getNotifications() {
		return JSON.parse(localStorage.getItem(this.key) || '[]');
	}

	saveNotifications(list) {
		localStorage.setItem(this.key, JSON.stringify(list));
		this.notifications = list;
		this.updateNotificationBadge();
	}

	addNotification(n) {
		const list = this.getNotifications();
		list.push(n);
		this.saveNotifications(list);
	}

	getUnreadCount() {
		return this.getNotifications().filter(n => n.status === 'pending').length;
	}

	updateNotificationBadge() {
		const badge = document.getElementById('notificationBadge');
		if (!badge) return;
		const count = this.getUnreadCount();
		badge.textContent = count > 9 ? '9+' : (count || '');
		badge.classList.toggle('hidden', count === 0);
	}

	// High-level helper used by UI. Replace with backend call when ready.
	async sendJoinRequest(courseCode, ownerName, currentUser) {
		const notification = {
			id: Date.now(),
			type: 'join_request',
			from: currentUser.name,
			to: ownerName,
			courseCode,
			timestamp: new Date().toISOString(),
			status: 'pending'
		};
		this.addNotification(notification);
		return notification;
	}
}

// expose global manager
window.notificationManager = new NotificationManager();
