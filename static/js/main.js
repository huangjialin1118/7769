// 主要的JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏Flash消息（只选择导航栏下方容器中的临时消息）
    setTimeout(function() {
        // 只选择Flash消息容器（.container.mt-3）中的alert，不影响页面其他部分的alert
        const flashAlerts = document.querySelectorAll('.container.mt-3 > .alert');
        flashAlerts.forEach(function(alert) {
            // 检查是否是flash消息（通常在导航栏下方）
            if (alert.closest('.container.mt-3') &&
                !alert.closest('.card') &&
                !alert.closest('.modal')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 3000);

    // 添加淡入动画效果
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.classList.add('fade-in');
        card.style.animationDelay = (index * 0.1) + 's';
    });
});

// 确认对话框功能
function confirmAction(message) {
    return confirm(message);
}

// 实时计算分摊金额（用于添加账单页面）
function calculateSplitAmount() {
    const amountInput = document.getElementById('amount');
    const checkboxes = document.querySelectorAll('input[name="participants"]:checked');
    const splitDisplay = document.getElementById('split-amount-display');

    if (amountInput && checkboxes.length > 0 && splitDisplay) {
        const amount = parseFloat(amountInput.value) || 0;
        const participantsCount = checkboxes.length;
        const splitAmount = participantsCount > 0 ? (amount / participantsCount).toFixed(2) : '0.00';

        splitDisplay.innerHTML = `
            <div class="alert alert-info">
                <strong>分摊计算：</strong><br>
                总金额：¥${amount.toFixed(2)}<br>
                参与人数：${participantsCount} 人<br>
                每人应付：¥${splitAmount}
            </div>
        `;
    }
}

// 格式化金额显示
function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

// 复制到剪贴板功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // 显示成功提示
        showToast('已复制到剪贴板');
    });
}

// 显示Toast提示
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        // 创建toast容器
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center text-bg-${type} border-0`;
    toastElement.setAttribute('role', 'alert');
    toastElement.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    document.getElementById('toast-container').appendChild(toastElement);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // 自动清理
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}