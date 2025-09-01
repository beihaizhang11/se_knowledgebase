// BDIC-SE Knowledge Base - Main JavaScript File

// Global configuration
const CONFIG = {
    API_BASE: '/api/v1',
    ITEMS_PER_PAGE: 10,
    ANIMATION_DURATION: 300
};

// Utility functions
const Utils = {
    // Debounce function for search inputs
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Format date
    formatDate: function(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('zh-CN', options);
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        // Add to container
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        container.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove element after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            container.removeChild(toast);
        });
    },

    // Handle API errors
    handleApiError: function(error, customMessage = null) {
        console.error('API Error:', error);
        const message = customMessage || '操作失败，请稍后重试';
        this.showToast(message, 'error');
    },

    // Loading spinner
    showLoading: function(element, text = '加载中...') {
        element.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">${text}</span>
                </div>
                <div class="mt-2 text-muted">${text}</div>
            </div>
        `;
    }
};

// API service
const API = {
    // Generic GET request
    get: async function(endpoint, params = {}) {
        const url = new URL(CONFIG.API_BASE + endpoint, window.location.origin);
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });

        try {
            const response = await fetch(url);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            Utils.handleApiError(error);
            throw error;
        }
    },

    // Generic POST request
    post: async function(endpoint, data = {}) {
        try {
            const response = await fetch(CONFIG.API_BASE + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || `HTTP ${response.status}`);
            }
            
            return result;
        } catch (error) {
            Utils.handleApiError(error);
            throw error;
        }
    },

    // Courses API
    courses: {
        getAll: (params = {}) => API.get('/courses', params),
        getById: (id) => API.get(`/courses/${id}`),
        getByStage: (stage) => API.get(`/courses/by-stage/${stage}`),
        getStats: () => API.get('/courses/stats'),
        search: (query) => API.get('/courses/search', { q: query })
    },

    // Instructors API
    instructors: {
        getAll: () => API.get('/instructors'),
        getById: (id) => API.get(`/instructors/${id}`),
        getCourses: (id, params = {}) => API.get(`/instructors/${id}/courses`, params)
    },

    // Reviews API
    reviews: {
        getByCourse: (courseId, params = {}) => API.get(`/courses/${courseId}/reviews`, params),
        getByUser: (userId, params = {}) => API.get(`/users/${userId}/reviews`, params),
        create: (data) => API.post('/reviews', data),
        checkEligibility: (data) => API.post('/reviews/check', data)
    },

    // Users API
    users: {
        login: (data) => API.post('/users/login', data),
        register: (data) => API.post('/users', data),
        checkUsername: (username) => API.get(`/users/check-username/${username}`),
        checkEmail: (email) => API.get(`/users/check-email/${email}`)
    }
};

// Search functionality
const Search = {
    init: function() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', 
                Utils.debounce(this.handleSearch.bind(this), 300)
            );
        }
    },

    handleSearch: async function(event) {
        const query = event.target.value.trim();
        const resultsContainer = document.getElementById('searchResults');
        
        if (query.length < 2) {
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }
            return;
        }

        try {
            const data = await API.courses.search(query);
            this.displayResults(data.data, resultsContainer);
        } catch (error) {
            // Error already handled by API service
        }
    },

    displayResults: function(courses, container) {
        if (!container) return;

        if (courses.length === 0) {
            container.innerHTML = `
                <div class="p-3 text-muted text-center">
                    <i class="fas fa-search mb-2"></i>
                    <div>未找到相关课程</div>
                </div>
            `;
            return;
        }

        const html = courses.map(course => `
            <div class="search-result-item p-3 border-bottom">
                <h6 class="mb-1">
                    <a href="/courses/${course.id}" class="text-decoration-none">
                        ${course.title}
                    </a>
                </h6>
                <small class="text-muted">
                    ${course.instructor ? course.instructor.name : ''} • 
                    ${course.stage} • 
                    ${course.average_rating.toFixed(1)} ⭐
                </small>
            </div>
        `).join('');

        container.innerHTML = html;
    }
};

// Form validation
const Validation = {
    email: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    password: function(password) {
        return password.length >= 6 && 
               /[a-zA-Z]/.test(password) && 
               /\d/.test(password);
    },

    required: function(value) {
        return value && value.trim().length > 0;
    }
};

// Authentication
const Auth = {
    init: function() {
        this.setupLoginForm();
        this.setupRegisterForm();
    },

    setupLoginForm: function() {
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }
    },

    setupRegisterForm: function() {
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', this.handleRegister.bind(this));
        }
    },

    handleLogin: async function(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = {
            email: formData.get('email'),
            password: formData.get('password')
        };

        try {
            const result = await API.users.login(data);
            Utils.showToast('登录成功！', 'success');
            
            // Store user data and redirect
            localStorage.setItem('user', JSON.stringify(result.data));
            window.location.reload();
        } catch (error) {
            // Error already handled by API service
        }
    },

    handleRegister: async function(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const data = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password')
        };

        // Client-side validation
        if (!Validation.required(data.username)) {
            Utils.showToast('请输入用户名', 'error');
            return;
        }

        if (!Validation.email(data.email)) {
            Utils.showToast('请输入有效的邮箱地址', 'error');
            return;
        }

        if (!Validation.password(data.password)) {
            Utils.showToast('密码至少6位，需包含字母和数字', 'error');
            return;
        }

        try {
            const result = await API.users.register(data);
            Utils.showToast('注册成功！请登录', 'success');
            
            // Switch to login modal
            const registerModal = bootstrap.Modal.getInstance(document.getElementById('registerModal'));
            const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
            
            registerModal.hide();
            setTimeout(() => loginModal.show(), 300);
        } catch (error) {
            // Error already handled by API service
        }
    },

    getCurrentUser: function() {
        const userData = localStorage.getItem('user');
        return userData ? JSON.parse(userData) : null;
    },

    logout: function() {
        localStorage.removeItem('user');
        Utils.showToast('已退出登录', 'info');
        window.location.reload();
    }
};

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize modules
    Search.init();
    Auth.init();
    
    // Setup global event listeners
    document.addEventListener('click', function(event) {
        // Handle logout clicks
        if (event.target.matches('[data-action="logout"]')) {
            event.preventDefault();
            Auth.logout();
        }
    });

    // Setup current user display
    const user = Auth.getCurrentUser();
    if (user) {
        // Update navigation to show user info
        const loginLink = document.querySelector('[data-bs-target="#loginModal"]');
        if (loginLink) {
            loginLink.innerHTML = `
                <i class="fas fa-user me-1"></i>
                ${user.username}
            `;
            loginLink.removeAttribute('data-bs-toggle');
            loginLink.removeAttribute('data-bs-target');
            loginLink.href = '#';
            loginLink.setAttribute('data-action', 'logout');
        }
    }
});

// Export for global access
window.KnowledgeBase = {
    Utils,
    API,
    Search,
    Auth,
    Validation
};
