// ===========================
// 室友记账系统 - 动画与交互系统
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    // ===========================
    // 0. 全局错误处理
    // ===========================
    window.addEventListener('error', function(e) {
        if (e.message && e.message.includes('modal')) {
            console.error('模态框错误:', e);
            // 不自动弹出alert，只在控制台记录
        }
    });

    // 检查Bootstrap是否正确加载
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap未正确加载');
        showToast('页面组件加载失败，请刷新页面', 'danger');
    }

    // ===========================
    // 1. 页面加载动画
    // ===========================
    initPageAnimations();

    // ===========================
    // 2. 导航栏滚动效果
    // ===========================
    initNavbarScroll();

    // ===========================
    // 3. 波纹点击效果
    // ===========================
    initRippleEffect();

    // ===========================
    // 4. 数字动画效果
    // ===========================
    initNumberAnimation();

    // ===========================
    // 5. 卡片观察器（进入视口动画）
    // ===========================
    initIntersectionObserver();

    // ===========================
    // 6. 平滑滚动
    // ===========================
    initSmoothScroll();

    // ===========================
    // 7. 自动隐藏Flash消息
    // ===========================
    setTimeout(function() {
        const flashAlerts = document.querySelectorAll('.container.mt-3 > .alert');
        flashAlerts.forEach(function(alert) {
            if (alert.closest('.container.mt-3') &&
                !alert.closest('.card') &&
                !alert.closest('.modal')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 3000);
});

// ===========================
// 页面加载动画初始化
// ===========================
function initPageAnimations() {
    // 给所有卡片添加进入动画（排除模态框内的卡片）
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        // 不影响模态框内的卡片
        if (!card.closest('.modal')) {
            card.classList.add('animate-in');
            card.style.animationDelay = `${index * 0.1}s`;
        }
    });

    // 给导航栏添加动画
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        navbar.style.animation = 'slideInDown 0.5s ease-out';
    }

    // 给按钮添加动画（排除卡片内和模态框内的按钮）
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach((btn, index) => {
        // 不影响卡片内和模态框内的按钮
        if (!btn.closest('.card') && !btn.closest('.modal')) {
            btn.style.opacity = '0';
            btn.style.animation = `fadeInUp 0.5s ease-out ${0.3 + index * 0.05}s forwards`;
        }
    });
}

// ===========================
// 导航栏滚动效果
// ===========================
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        // 添加滚动类
        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // 隐藏/显示导航栏
        if (currentScroll > lastScroll && currentScroll > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }

        lastScroll = currentScroll;
    });
}

// ===========================
// 简化的按钮点击效果
// ===========================
function initRippleEffect() {
    // 简化版：仅确保按钮有合适的样式
    document.querySelectorAll('.btn').forEach(btn => {
        btn.style.position = 'relative';
        btn.style.overflow = 'hidden';
        btn.style.transformOrigin = 'center';
    });
}

// ===========================
// 数字动画效果
// ===========================
function initNumberAnimation() {
    const animateValue = (element, start, end, duration) => {
        const startTimestamp = Date.now();
        const step = () => {
            const timestamp = Date.now();
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const easeProgress = easeOutQuart(progress);
            const current = Math.floor(easeProgress * (end - start) + start);

            element.textContent = formatNumber(current);

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                element.textContent = formatNumber(end);
            }
        };
        step();
    };

    // 缓动函数
    const easeOutQuart = (t) => 1 - Math.pow(1 - t, 4);

    // 格式化数字
    const formatNumber = (num) => {
        if (element.dataset.format === 'currency') {
            return `¥${num.toFixed(2)}`;
        }
        return num.toString();
    };

    // 查找所有需要动画的数字
    const numberElements = document.querySelectorAll('[data-animate-number]');
    numberElements.forEach(element => {
        const finalValue = parseFloat(element.dataset.animateNumber);
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateValue(element, 0, finalValue, 1000);
                    observer.unobserve(element);
                }
            });
        });
        observer.observe(element);
    });
}

// ===========================
// 交叉观察器（元素进入视口时动画）
// ===========================
function initIntersectionObserver() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.classList.add('visible');
                    entry.target.style.animation = 'fadeInUp 0.6s ease-out forwards';
                }, index * 100);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // 观察所有需要动画的元素
    document.querySelectorAll('.observe-animate').forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
}

// ===========================
// 平滑滚动增强
// ===========================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ===========================
// 原有功能函数保留
// ===========================

// 确认对话框功能
function confirmAction(message) {
    return confirm(message);
}

// 实时计算分摊金额
function calculateSplitAmount() {
    const amountInput = document.getElementById('amount');
    const checkboxes = document.querySelectorAll('input[name="participants"]:checked');
    const splitDisplay = document.getElementById('split-amount-display');

    if (amountInput && checkboxes.length > 0 && splitDisplay) {
        const amount = parseFloat(amountInput.value) || 0;
        const participantsCount = checkboxes.length;
        const splitAmount = participantsCount > 0 ? (amount / participantsCount).toFixed(2) : '0.00';

        splitDisplay.innerHTML = `
            <div class="alert alert-info glass-effect">
                <strong>分摊计算：</strong><br>
                总金额：<span data-animate-number="${amount}" data-format="currency">¥${amount.toFixed(2)}</span><br>
                参与人数：${participantsCount} 人<br>
                每人应付：<span class="text-primary fw-bold">¥${splitAmount}</span>
            </div>
        `;

        // 重新初始化数字动画
        initNumberAnimation();
    }
}

// 格式化金额显示
function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

// 复制到剪贴板功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('已复制到剪贴板');
    });
}

// 安全的模态框管理
function safeShowModal(modalId) {
    try {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) {
            console.error(`模态框 ${modalId} 不存在`);
            return null;
        }

        // 使用Bootstrap的getOrCreateInstance方法
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement, {
            backdrop: true,
            keyboard: true,
            focus: true
        });

        // 强制重置内部状态，确保模态框能正常显示
        modal._isShown = false;
        modal._isTransitioning = false;

        return modal;
    } catch (error) {
        console.error('模态框创建失败:', error);
        alert('模态框加载失败，请刷新页面重试');
        return null;
    }
}

// 显示Toast提示（增强版）
function showToast(message, type = 'success') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    const toastElement = document.createElement('div');
    toastElement.className = `toast align-items-center border-0 glass-effect`;
    toastElement.setAttribute('role', 'alert');

    // 根据类型设置颜色
    let iconClass = '';
    let colorClass = '';
    switch(type) {
        case 'success':
            iconClass = 'bi-check-circle-fill';
            colorClass = 'text-success';
            break;
        case 'danger':
            iconClass = 'bi-exclamation-triangle-fill';
            colorClass = 'text-danger';
            break;
        case 'warning':
            iconClass = 'bi-exclamation-circle-fill';
            colorClass = 'text-warning';
            break;
        default:
            iconClass = 'bi-info-circle-fill';
            colorClass = 'text-info';
    }

    toastElement.innerHTML = `
        <div class="d-flex align-items-center p-2">
            <i class="bi ${iconClass} ${colorClass} fs-4 me-2"></i>
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    // 添加进入动画
    toastElement.style.animation = 'slideInRight 0.3s ease-out';

    toastContainer.appendChild(toastElement);
    const toast = new bootstrap.Toast(toastElement, {
        delay: 3000
    });
    toast.show();

    // 自动清理
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => {
            toastElement.remove();
        }, 300);
    });
}

// ===========================
// 辅助动画样式注入
// ===========================
const animationStyles = `
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

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes scaleIn {
        from {
            transform: scale(0.8);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }
`;

// 注入动画样式
const styleElement = document.createElement('style');
styleElement.textContent = animationStyles;
document.head.appendChild(styleElement);

// ===========================
// 页面加载进度条
// ===========================
window.addEventListener('load', () => {
    // 创建加载完成动画
    const loader = document.createElement('div');
    loader.className = 'page-loader';
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: var(--primary-gradient);
        z-index: 9999;
        animation: loadingBar 0.5s ease-out forwards;
    `;

    document.body.appendChild(loader);

    const loadingBarAnimation = `
        @keyframes loadingBar {
            0% { width: 0; }
            100% { width: 100%; opacity: 0; }
        }
    `;

    const style = document.createElement('style');
    style.textContent = loadingBarAnimation;
    document.head.appendChild(style);

    setTimeout(() => {
        loader.remove();
    }, 500);
});