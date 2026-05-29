// Initialize global ElMessage from Element Plus CDN
if (typeof ElementPlus !== 'undefined' && ElementPlus.ElMessage) {
    window.ElMessage = ElementPlus.ElMessage;
    window.ElMessageBox = ElementPlus.ElMessageBox;
}
// Fallback if ElementPlus not loaded
if (!window.ElMessage) {
    window.ElMessage = { error: (m) => alert(m), warning: (m) => alert(m), success: (m) => alert(m) };
    window.ElMessageBox = { confirm: () => Promise.resolve() };
}

const API_BASE = '/api';

function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function clearToken() {
    localStorage.removeItem('token');
}

async function apiRequest(url, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };
    if (options.body instanceof FormData) {
        delete headers['Content-Type'];
    }
    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers,
    });
    if (response.status === 401) {
        clearToken();
        ElMessage.error('登录已过期，请重新登录');
        setTimeout(() => { window.location.href = '/login'; }, 1500);
        throw new Error('Unauthorized');
    }
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        ElMessage.error(error.detail || '请求失败');
        throw new Error(error.detail || 'Request failed');
    }
    return response.json();
}

async function getApi(url, params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
            query.append(k, v);
        }
    });
    const qs = query.toString();
    return apiRequest(url + (qs ? `?${qs}` : ''));
}

async function postApi(url, data) {
    return apiRequest(url, { method: 'POST', body: JSON.stringify(data) });
}

async function putApi(url, data) {
    return apiRequest(url, { method: 'PUT', body: JSON.stringify(data) });
}

async function deleteApi(url) {
    return apiRequest(url, { method: 'DELETE' });
}

async function uploadApi(url, formData) {
    return apiRequest(url, { method: 'POST', body: formData });
}

function checkAuth() {
    if (!getToken()) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

function formatDate(d) {
    if (!d) return '';
    return new Date(d).toLocaleDateString('zh-CN');
}

const COOP_TYPE_LABELS = {
    keynote: '主讲嘉宾',
    committee: '程序委员会',
    session_chair: '分会主席',
    general_chair: '大会主席',
    editor: '论文集编辑',
    other: '其他',
};

const CONF_STATUS_LABELS = {
    planned: '计划中',
    ongoing: '进行中',
    completed: '已结束',
};

const SUB_STATUS_LABELS = {
    pending: '待分配',
    assigned: '已分配',
    confirmed: '已确认',
};
