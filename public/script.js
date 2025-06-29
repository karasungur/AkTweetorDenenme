// AkTweetor Web Interface JavaScript

// Initialize the application
document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 AkTweetor Web Interface Loaded");
  checkStatus();
});

// Check application status
async function checkStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    console.log("📊 Status:", data);

    // Update status display if needed
    const statusMessage = document.querySelector(".status-message");
    if (statusMessage && data.message) {
      statusMessage.textContent = data.message;
    }
  } catch (error) {
    console.error("❌ Status check failed:", error);
  }
}

// Feature button handlers
function showLogin() {
  showNotification("Giriş yapma özelliği geliştiriliyor...", "info");
  console.log("🔐 Login feature clicked");
}

function showProfiles() {
  showNotification("Profil yönetimi özelliği geliştiriliyor...", "info");
  console.log("👤 Profiles feature clicked");
}

function showAutomation() {
  showNotification("Otomasyon özelliği geliştiriliyor...", "info");
  console.log("🤖 Automation feature clicked");
}

function showSettings() {
  showNotification("Ayarlar özelliği geliştiriliyor...", "info");
  console.log("⚙️ Settings feature clicked");
}

// Notification system
function showNotification(message, type = "info") {
  // Remove existing notification
  const existingNotification = document.querySelector(".notification");
  if (existingNotification) {
    existingNotification.remove();
  }

  // Create notification element
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                ✕
            </button>
        </div>
    `;

  // Add notification styles
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        max-width: 400px;
        animation: slideInRight 0.3s ease;
    `;

  // Add type-specific styling
  if (type === "info") {
    notification.style.borderLeft = "4px solid #0072CE";
  } else if (type === "success") {
    notification.style.borderLeft = "4px solid #388E3C";
  } else if (type === "error") {
    notification.style.borderLeft = "4px solid #D32F2F";
  }

  // Style the content
  const content = notification.querySelector(".notification-content");
  content.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 15px;
    `;

  const closeBtn = notification.querySelector(".notification-close");
  closeBtn.style.cssText = `
        background: none;
        border: none;
        font-size: 16px;
        cursor: pointer;
        color: #666;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    `;

  // Add animation keyframes if not already added
  if (!document.getElementById("notification-styles")) {
    const style = document.createElement("style");
    style.id = "notification-styles";
    style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
    document.head.appendChild(style);
  }

  // Add to page
  document.body.appendChild(notification);

  // Auto remove after 5 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.style.animation = "slideInRight 0.3s ease reverse";
      setTimeout(() => notification.remove(), 300);
    }
  }, 5000);
}

// Add some interactivity to cards
document.addEventListener("DOMContentLoaded", function () {
  const cards = document.querySelectorAll(".feature-card");

  cards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.background =
        "linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)";
    });

    card.addEventListener("mouseleave", function () {
      this.style.background = "white";
    });
  });
});

// Console welcome message
console.log(`
🌟 AkTweetor Web Interface
📱 Web version of the Twitter automation tool
💻 Original desktop app built with PyQt5
🌐 Adapted for web environment
`);
