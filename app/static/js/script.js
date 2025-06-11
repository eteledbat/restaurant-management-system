// 基本的JavaScript功能

// 自动隐藏alert消息
document.addEventListener('DOMContentLoaded', function() {
  // 5秒后自动隐藏alert
  setTimeout(function() {
      const alerts = document.querySelectorAll('.alert');
      alerts.forEach(function(alert) {
          alert.style.opacity = '0';
          setTimeout(function() {
              alert.remove();
          }, 300);
      });
  }, 5000);
});