// 主应用逻辑
const API_BASE = '/api';

// 全局状态
const AppState = {
    currentPage: 'dashboard',
    recordsPage: 1,
    recordsPerPage: 20,
    classList: [],
};

// API 请求封装
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${url}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: '请求失败' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API请求失败:', error);
        showToast(error.message || '网络请求失败', 'error');
        throw error;
    }
}

// 页面导航
function navigateTo(page) {
    AppState.currentPage = page;

    // 更新导航高亮
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    // 显示对应页面
    document.querySelectorAll('.page').forEach(p => {
        p.classList.toggle('active', p.id === `page-${page}`);
    });

    // 更新标题
    const titles = {
        dashboard: ['仪表盘', '系统运行概览'],
        detection: ['物料检测', '上传图像进行智能识别与分拣'],
        inventory: ['库存管理', '管理仓储物料库存'],
        sensor: ['传感器数据', '查看传感器实时数据'],
        records: ['检测记录', '查看历史检测记录'],
        settings: ['系统设置', '配置系统参数'],
    };
    const [title, subtitle] = titles[page] || ['', ''];
    document.getElementById('page-title').textContent = title;
    document.getElementById('page-subtitle').textContent = subtitle;

    // 页面特定初始化
    if (page === 'dashboard') loadDashboard();
    if (page === 'inventory') loadInventory();
    if (page === 'sensor') loadSensorData();
    if (page === 'records') loadRecords();
    if (page === 'settings') loadSystemInfo();
}

// Toast 通知
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 模态框
function showModal(title, bodyContent, footerButtons = []) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyContent;

    const footer = document.getElementById('modal-footer');
    footer.innerHTML = '';
    footerButtons.forEach(btn => {
        const button = document.createElement('button');
        button.className = `btn ${btn.class || ''}`;
        button.textContent = btn.text;
        button.onclick = btn.onClick;
        footer.appendChild(button);
    });

    document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

// 格式化时间
function formatTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

// 获取融合结果徽章
function getFusionBadge(status) {
    const map = {
        pass: 'badge-pass',
        warning: 'badge-warning',
        reject: 'badge-reject',
    };
    const textMap = {
        pass: '通过',
        warning: '警告',
        reject: '拒绝',
    };
    return `<span class="badge ${map[status] || 'badge-pending'}">${textMap[status] || status || '-'}</span>`;
}

// 获取分拣状态徽章
function getSortBadge(status) {
    const map = {
        pending: 'badge-pending',
        sorting: 'badge-sorting',
        sorted: 'badge-sorted',
        failed: 'badge-failed',
    };
    const textMap = {
        pending: '待分拣',
        sorting: '分拣中',
        sorted: '已分拣',
        failed: '失败',
    };
    return `<span class="badge ${map[status] || 'badge-pending'}">${textMap[status] || status || '-'}</span>`;
}

// 获取异常徽章
function getAnomalyBadge(isAnomaly, level) {
    if (isAnomaly) {
        return `<span class="badge badge-anomaly">${level === 'severe' ? '严重' : '轻度'}</span>`;
    }
    return '<span class="badge badge-normal">正常</span>';
}

// 加载类别列表
async function loadClassList() {
    try {
        const data = await apiRequest('/stats/classes');
        AppState.classList = data.classes;

        // 填充记录筛选下拉
        const select = document.getElementById('record-class-filter');
        if (select) {
            data.classes.forEach(c => {
                const option = document.createElement('option');
                option.value = c.class_id;
                option.textContent = `${c.class_name_cn} (${c.class_name})`;
                select.appendChild(option);
            });
        }
    } catch (e) {
        console.error('加载类别列表失败:', e);
    }
}

// 更新当前时间
function updateCurrentTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString('zh-CN');
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 导航点击
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(item.dataset.page);
        });
    });

    // 刷新按钮
    document.getElementById('btn-refresh').addEventListener('click', () => {
        navigateTo(AppState.currentPage);
        showToast('数据已刷新', 'success');
    });

    // 模态框关闭
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
        if (e.target.id === 'modal-overlay') closeModal();
    });

    // 时间更新
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    // 加载类别列表
    loadClassList();

    // 初始加载仪表盘
    loadDashboard();
});
