/**
 * Course Detail Page JavaScript
 * Steam-style course page functionality
 */

class CourseDetail {
    constructor() {
        this.courseId = null;
        this.currentImageIndex = 0;
        this.images = [];
        this.currentPage = 1;
        this.selectedRating = 0;
        this.isLoading = false;
    }

    static init(courseId) {
        const instance = new CourseDetail();
        instance.courseId = courseId;
        instance.initializeComponents();
        return instance;
    }

    initializeComponents() {
        this.loadCourseImages();
        this.loadReviews();
        this.loadRelatedCourses();
        this.setupEventListeners();
        this.generateRatingStars();
        this.setupStarRating();
    }

    setupEventListeners() {
        // Review sort change
        const reviewSort = document.getElementById('reviewSort');
        if (reviewSort) {
            reviewSort.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadReviews();
            });
        }

        // Modal events
        const reviewModal = document.getElementById('reviewModal');
        if (reviewModal) {
            reviewModal.addEventListener('hidden.bs.modal', () => {
                this.resetReviewForm();
            });
        }
    }

    loadCourseImages() {
        // Mock image data - in real app, fetch from API
        this.images = [
            '/static/img/course-placeholder-1.jpg',
            '/static/img/course-placeholder-2.jpg',
            '/static/img/course-placeholder-3.jpg'
        ];

        this.displayMainImage(0);
        this.generateThumbnails();
    }

    displayMainImage(index) {
        const mainImage = document.getElementById('mainCourseImage');
        if (mainImage && this.images.length > 0) {
            this.currentImageIndex = index;
            
            if (this.images[index]) {
                mainImage.style.backgroundImage = `url('${this.images[index]}')`;
                mainImage.innerHTML = '';
            } else {
                mainImage.style.backgroundImage = '';
                mainImage.innerHTML = `
                    <div style="text-align: center;">
                        <i class="fas fa-image" style="font-size: 3rem; margin-bottom: 10px; opacity: 0.5;"></i>
                        <div>暂无课程图片</div>
                    </div>
                `;
            }
        }
    }

    generateThumbnails() {
        const thumbnailStrip = document.getElementById('thumbnailStrip');
        if (!thumbnailStrip) return;

        thumbnailStrip.innerHTML = '';
        
        this.images.forEach((image, index) => {
            const thumbnail = document.createElement('div');
            thumbnail.className = `thumbnail ${index === 0 ? 'active' : ''}`;
            thumbnail.style.backgroundImage = `url('${image}')`;
            thumbnail.style.backgroundSize = 'cover';
            thumbnail.style.backgroundPosition = 'center';
            
            thumbnail.addEventListener('click', () => {
                this.displayMainImage(index);
                this.updateActiveThumbnail(index);
            });
            
            thumbnailStrip.appendChild(thumbnail);
        });
    }

    updateActiveThumbnail(index) {
        const thumbnails = document.querySelectorAll('.thumbnail');
        thumbnails.forEach((thumb, i) => {
            thumb.classList.toggle('active', i === index);
        });
    }

    generateRatingStars() {
        const starsContainer = document.querySelector('.stars-container');
        if (!starsContainer) return;

        // Get rating from course data (this would come from the template)
        const ratingElement = document.querySelector('.score-number');
        const rating = ratingElement ? parseFloat(ratingElement.textContent) : 0;

        starsContainer.innerHTML = '';
        
        for (let i = 1; i <= 5; i++) {
            const star = document.createElement('i');
            star.className = i <= rating ? 'fas fa-star star' : 'far fa-star star empty';
            starsContainer.appendChild(star);
        }
    }

    setupStarRating() {
        const starInputs = document.querySelectorAll('#starRatingInput i');
        const ratingText = document.getElementById('ratingText');
        
        const ratingTexts = {
            1: '很差 - 不推荐',
            2: '较差 - 有待改进',
            3: '一般 - 还可以',
            4: '不错 - 值得推荐',
            5: '优秀 - 强烈推荐'
        };

        starInputs.forEach((star, index) => {
            const rating = index + 1;
            
            star.addEventListener('mouseenter', () => {
                this.highlightStars(rating);
                if (ratingText) {
                    ratingText.textContent = ratingTexts[rating];
                }
            });
            
            star.addEventListener('mouseleave', () => {
                this.highlightStars(this.selectedRating);
                if (ratingText) {
                    ratingText.textContent = this.selectedRating > 0 
                        ? ratingTexts[this.selectedRating]
                        : '点击星星评分';
                }
            });
            
            star.addEventListener('click', () => {
                this.selectedRating = rating;
                this.highlightStars(rating);
                if (ratingText) {
                    ratingText.textContent = ratingTexts[rating];
                }
            });
        });
    }

    highlightStars(rating) {
        const starInputs = document.querySelectorAll('#starRatingInput i');
        starInputs.forEach((star, index) => {
            if (index < rating) {
                star.className = 'fas fa-star active';
            } else {
                star.className = 'far fa-star';
            }
        });
    }

    async loadReviews() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const reviewsContainer = document.getElementById('reviewsContainer');
        const sort = document.getElementById('reviewSort')?.value || 'newest';
        
        if (this.currentPage === 1) {
            reviewsContainer.innerHTML = `
                <div class="loading-reviews">
                    <i class="fas fa-spinner fa-spin"></i>
                    加载评价中...
                </div>
            `;
        }

        try {
            const response = await fetch(`/api/v1/courses/${this.courseId}/reviews?page=${this.currentPage}&sort=${sort}`);
            const data = await response.json();
            
            if (data.success) {
                if (this.currentPage === 1) {
                    reviewsContainer.innerHTML = '';
                    this.updateRatingBreakdown(data.data.rating_distribution);
                }
                
                this.renderReviews(data.data.reviews, this.currentPage === 1);
                this.updateLoadMoreButton(data.pagination);
            } else {
                throw new Error(data.message || '加载失败');
            }
        } catch (error) {
            console.error('Error loading reviews:', error);
            reviewsContainer.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    加载评价失败，请稍后重试
                </div>
            `;
        } finally {
            this.isLoading = false;
        }
    }

    renderReviews(reviews, replace = false) {
        const reviewsContainer = document.getElementById('reviewsContainer');
        if (!reviewsContainer) return;

        if (replace) {
            reviewsContainer.innerHTML = '';
        }

        if (reviews.length === 0 && replace) {
            reviewsContainer.innerHTML = `
                <div class="no-reviews">
                    <i class="fas fa-comments" style="font-size: 3rem; opacity: 0.3; margin-bottom: 15px;"></i>
                    <p>暂无评价，成为第一个评价的人吧！</p>
                </div>
            `;
            return;
        }

        reviews.forEach(review => {
            const reviewCard = this.createReviewCard(review);
            reviewsContainer.appendChild(reviewCard);
        });
    }

    createReviewCard(review) {
        const card = document.createElement('div');
        card.className = 'review-card';
        
        const userAvatar = review.user?.avatar_url || '/static/img/default-avatar.png';
        const userName = review.user?.username || '匿名用户';
        const reviewDate = new Date(review.created_at).toLocaleDateString('zh-CN');
        
        // Generate rating stars
        let starsHtml = '';
        if (review.rating) {
            for (let i = 1; i <= 5; i++) {
                starsHtml += `<i class="fas fa-star ${i <= review.rating ? 'star' : 'star empty'}"></i>`;
            }
        }
        
        card.innerHTML = `
            <div class="review-header">
                <div class="review-user">
                    <img src="${userAvatar}" alt="${userName}" class="review-avatar">
                    <div>
                        <div class="review-username">${userName}</div>
                        <div class="review-date">${reviewDate}</div>
                    </div>
                </div>
                ${review.rating ? `
                    <div class="review-rating">
                        ${starsHtml}
                        <span class="rating-number">${review.rating}/5</span>
                    </div>
                ` : ''}
            </div>
            ${review.content ? `
                <div class="review-content">${this.escapeHtml(review.content)}</div>
            ` : ''}
        `;
        
        return card;
    }

    updateRatingBreakdown(distribution) {
        const breakdownContainer = document.getElementById('ratingBreakdown');
        if (!breakdownContainer || !distribution) return;

        const totalRatings = distribution.reduce((sum, item) => sum + item.count, 0);
        
        breakdownContainer.innerHTML = '';
        
        for (let rating = 5; rating >= 1; rating--) {
            const item = distribution.find(d => d.rating === rating);
            const count = item ? item.count : 0;
            const percentage = totalRatings > 0 ? (count / totalRatings * 100) : 0;
            
            const barElement = document.createElement('div');
            barElement.className = 'rating-bar';
            barElement.innerHTML = `
                <span>${rating}★</span>
                <div class="rating-bar-fill">
                    <div class="rating-bar-progress" style="width: ${percentage}%"></div>
                </div>
                <span>${count}</span>
            `;
            
            breakdownContainer.appendChild(barElement);
        }
    }

    updateLoadMoreButton(pagination) {
        const loadMoreContainer = document.getElementById('loadMoreContainer');
        if (!loadMoreContainer) return;

        if (pagination.has_next) {
            loadMoreContainer.style.display = 'block';
        } else {
            loadMoreContainer.style.display = 'none';
        }
    }

    async loadRelatedCourses() {
        const relatedContainer = document.getElementById('relatedCourses');
        if (!relatedContainer) return;

        try {
            // Mock data for related courses
            const mockRelatedCourses = [
                {
                    id: 1,
                    title: '数据结构与算法',
                    instructor: { name: '张教授' },
                    average_rating: 4.5
                },
                {
                    id: 2,
                    title: '计算机网络',
                    instructor: { name: '李教授' },
                    average_rating: 4.2
                },
                {
                    id: 3,
                    title: '操作系统',
                    instructor: { name: '王教授' },
                    average_rating: 4.0
                }
            ];

            relatedContainer.innerHTML = '';
            
            mockRelatedCourses.forEach(course => {
                const courseElement = document.createElement('div');
                courseElement.className = 'related-course';
                courseElement.innerHTML = `
                    <div class="related-course-image"></div>
                    <div class="related-course-info">
                        <div class="related-course-title">${course.title}</div>
                        <div class="related-course-instructor">${course.instructor.name}</div>
                    </div>
                `;
                
                courseElement.addEventListener('click', () => {
                    window.location.href = `/courses/${course.id}`;
                });
                
                relatedContainer.appendChild(courseElement);
            });
        } catch (error) {
            console.error('Error loading related courses:', error);
            relatedContainer.innerHTML = `
                <div class="error-message">加载相关课程失败</div>
            `;
        }
    }

    resetReviewForm() {
        this.selectedRating = 0;
        this.highlightStars(0);
        
        const ratingText = document.getElementById('ratingText');
        const reviewContent = document.getElementById('reviewContent');
        
        if (ratingText) {
            ratingText.textContent = '点击星星评分';
        }
        
        if (reviewContent) {
            reviewContent.value = '';
        }
    }

    async submitReview() {
        const content = document.getElementById('reviewContent')?.value?.trim();
        
        if (this.selectedRating === 0) {
            alert('请选择评分');
            return;
        }

        // User ID will be determined by the server from the authenticated session
        const reviewData = {
            rating: this.selectedRating,
            content: content || null
        };

        try {
            const response = await fetch(`/api/v1/courses/${this.courseId}/reviews`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(reviewData)
            });

            const data = await response.json();
            
            if (data.success) {
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('reviewModal'));
                modal.hide();
                
                // Reload reviews
                this.currentPage = 1;
                await this.loadReviews();
                
                // Show success message
                this.showToast('评价提交成功！', 'success');
                
                // Update course rating (you might want to reload the page or update the display)
                location.reload();
            } else {
                throw new Error(data.message || '提交失败');
            }
        } catch (error) {
            console.error('Error submitting review:', error);
            alert('提交评价失败: ' + error.message);
        }
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--steam-bg-medium);
            color: var(--steam-text-light);
            padding: 15px 20px;
            border-radius: 8px;
            border: 1px solid var(--steam-border);
            z-index: 9999;
            box-shadow: var(--steam-shadow);
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for template
window.CourseDetail = CourseDetail;

window.previousImage = function() {
    const instance = window.courseDetailInstance;
    if (instance && instance.images.length > 0) {
        const newIndex = (instance.currentImageIndex - 1 + instance.images.length) % instance.images.length;
        instance.displayMainImage(newIndex);
        instance.updateActiveThumbnail(newIndex);
    }
};

window.nextImage = function() {
    const instance = window.courseDetailInstance;
    if (instance && instance.images.length > 0) {
        const newIndex = (instance.currentImageIndex + 1) % instance.images.length;
        instance.displayMainImage(newIndex);
        instance.updateActiveThumbnail(newIndex);
    }
};

window.showReviewModal = function() {
    const modal = new bootstrap.Modal(document.getElementById('reviewModal'));
    modal.show();
};

window.submitReview = function() {
    const instance = window.courseDetailInstance;
    if (instance) {
        instance.submitReview();
    }
};

window.loadMoreReviews = function() {
    const instance = window.courseDetailInstance;
    if (instance) {
        instance.currentPage++;
        instance.loadReviews();
    }
};

window.shareContent = function() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('链接已复制到剪贴板');
        });
    }
};

// Store instance globally for template functions
document.addEventListener('DOMContentLoaded', function() {
    // This will be called by the template with the course ID
});
