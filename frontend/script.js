class StarGiftsApp {
    constructor() {
        this.apiBase = window.location.hostname.includes('vercel.app') 
            ? '/api' 
            : 'http://localhost:5000/api';
        
        this.currentPage = 1;
        this.currentCategory = '';
        this.currentSort = 'newest';
        this.searchQuery = '';
        
        this.init();
    }
    
    async init() {
        this.bindEvents();
        await this.loadStats();
        await this.loadCollections();
        await this.loadCategories();
    }
    
    bindEvents() {
        // Search
        document.getElementById('searchBtn').addEventListener('click', () => this.search());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });
        
        // Filters
        document.getElementById('categoryFilter').addEventListener('change', (e) => {
            this.currentCategory = e.target.value;
            this.currentPage = 1;
            this.loadCollections();
        });
        
        document.getElementById('sortFilter').addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.currentPage = 1;
            this.loadCollections();
        });
        
        // Modal
        const modal = document.getElementById('collectionModal');
        const closeBtn = document.querySelector('.close');
        
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
    
    async loadStats() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('totalCollections').textContent = 
                    data.data.total_collections.toLocaleString();
                document.getElementById('totalGifts').textContent = 
                    data.data.total_items.toLocaleString();
                document.getElementById('totalCategories').textContent = 
                    data.data.categories.toLocaleString();
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }
    
    async loadCollections() {
        const grid = document.getElementById('collectionsGrid');
        const loading = document.getElementById('collectionsLoading');
        
        grid.innerHTML = '';
        loading.style.display = 'block';
        
        try {
            let url = `${this.apiBase}/collections`;
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                loading.style.display = 'none';
                this.renderCollections(data.data);
            } else {
                loading.innerHTML = `<p class="error">❌ ${data.error}</p>`;
            }
        } catch (error) {
            console.error('Error loading collections:', error);
            loading.innerHTML = `<p class="error">❌ فشل في تحميل البيانات</p>`;
        }
    }
    
    renderCollections(collections) {
        const grid = document.getElementById('collectionsGrid');
        
        if (collections.length === 0) {
            grid.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-box-open fa-3x"></i>
                    <h3>لا توجد مجموعات</h3>
                    <p>لم يتم العثور على مجموعات هدايا.</p>
                </div>
            `;
            return;
        }
        
        collections.forEach(collection => {
            const card = document.createElement('div');
            card.className = 'collection-card';
            card.innerHTML = `
                <div class="collection-image">
                    <img src="${collection.photo_url || 'assets/default-collection.jpg'}" 
                         alt="${collection.title}" 
                         onerror="this.src='assets/default-collection.jpg'">
                    <div class="collection-badge">${collection.category || 'عام'}</div>
                </div>
                <div class="collection-content">
                    <h3 class="collection-title">
                        ${collection.title}
                        <i class="fas fa-star"></i>
                    </h3>
                    <p class="collection-description">${collection.description || 'لا يوجد وصف'}</p>
                    <div class="collection-stats">
                        <div class="stat-item">
                            <span class="count">${collection.items_count || 0}</span>
                            <span class="label">عنصر</span>
                        </div>
                        <div class="stat-item">
                            <span class="count">${collection.stats?.average_price || 0}</span>
                            <span class="label">متوسط السعر</span>
                        </div>
                        <div class="collection-price">
                            ${collection.price_range?.min || 0} - ${collection.price_range?.max || 0} $
                        </div>
                    </div>
                </div>
            `;
            
            card.addEventListener('click', () => this.openCollectionModal(collection.id));
            grid.appendChild(card);
        });
    }
    
    async openCollectionModal(collectionId) {
        const modal = document.getElementById('collectionModal');
        const content = document.getElementById('modalContent');
        
        content.innerHTML = `
            <div class="modal-loading">
                <div class="spinner"></div>
                <p>جاري تحميل التفاصيل...</p>
            </div>
        `;
        
        modal.style.display = 'block';
        
        try {
            const [collectionRes, itemsRes] = await Promise.all([
                fetch(`${this.apiBase}/collection/${collectionId}`),
                fetch(`${this.apiBase}/collection/${collectionId}/items?page=1&limit=20`)
            ]);
            
            const collectionData = await collectionRes.json();
            const itemsData = await itemsRes.json();
            
            if (collectionData.success && itemsData.success) {
                this.renderModalContent(collectionData.data, itemsData.data);
            } else {
                content.innerHTML = `
                    <div class="modal-error">
                        <i class="fas fa-exclamation-triangle fa-2x"></i>
                        <h3>خطأ في التحميل</h3>
                        <p>${collectionData.error || itemsData.error}</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading collection details:', error);
            content.innerHTML = `
                <div class="modal-error">
                    <i class="fas fa-exclamation-triangle fa-2x"></i>
                    <h3>خطأ في التحميل</h3>
                    <p>فشل في تحميل تفاصيل المجموعة</p>
                </div>
            `;
        }
    }
    
    renderModalContent(collection, items) {
        const content = document.getElementById('modalContent');
        
        content.innerHTML = `
            <div class="modal-header">
                <h2><i class="fas fa-gift"></i> ${collection.title}</h2>
                <div class="modal-tags">
                    <span class="tag">${collection.category}</span>
                    <span class="tag price-tag">${collection.price_range?.min || 0} - ${collection.price_range?.max || 0} $</span>
                </div>
            </div>
            
            <div class="modal-body">
                <div class="collection-info">
                    <div class="collection-image-large">
                        <img src="${collection.cover_url || collection.photo_url || 'assets/default-collection.jpg'}" 
                             alt="${collection.title}">
                    </div>
                    <div class="collection-details">
                        <p class="description">${collection.description || 'لا يوجد وصف'}</p>
                        
                        <div class="stats-grid">
                            <div class="stat-box">
                                <i class="fas fa-boxes"></i>
                                <div>
                                    <span class="stat-value">${collection.items_count || 0}</span>
                                    <span class="stat-label">إجمالي العناصر</span>
                                </div>
                            </div>
                            <div class="stat-box">
                                <i class="fas fa-chart-line"></i>
                                <div>
                                    <span class="stat-value">${collection.stats?.popularity || 0}%</span>
                                    <span class="stat-label">الشعبية</span>
                                </div>
                            </div>
                            <div class="stat-box">
                                <i class="fas fa-calendar"></i>
                                <div>
                                    <span class="stat-value">${new Date(collection.created_at).toLocaleDateString('ar-EG')}</span>
                                    <span class="stat-label">تاريخ الإضافة</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="items-section">
                    <h3><i class="fas fa-shopping-bag"></i> العناصر المتاحة (${items.length})</h3>
                    
                    <div class="items-grid">
                        ${items.map(item => `
                            <div class="item-card">
                                <div class="item-image">
                                    <img src="${item.image_url || 'assets/default-item.jpg'}" 
                                         alt="${item.title || 'عنصر'}">
                                    ${item.animation_url ? 
                                        `<div class="item-badge animate-badge">
                                            <i class="fas fa-play-circle"></i> متحرك
                                        </div>` : ''}
                                </div>
                                <div class="item-info">
                                    <h4>${item.title || 'عنصر بدون عنوان'}</h4>
                                    <p class="item-price">${item.formatted_price || '0.00 $'}</p>
                                    <div class="item-meta">
                                        <span><i class="fas fa-hashtag"></i> ${item.id}</span>
                                        <span><i class="fas fa-clock"></i> ${new Date(item.date).toLocaleDateString('ar-EG')}</span>
                                    </div>
                                    <button class="preview-btn" onclick="app.previewItem(${item.id})">
                                        <i class="fas fa-eye"></i> معاينة
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    async search() {
        const query = document.getElementById('searchInput').value.trim();
        
        if (!query) {
            this.searchQuery = '';
            this.loadCollections();
            return;
        }
        
        this.searchQuery = query;
        
        try {
            const response = await fetch(`${this.apiBase}/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSearchResults(data.data);
            }
        } catch (error) {
            console.error('Error searching:', error);
        }
    }
    
    renderSearchResults(results) {
        const grid = document.getElementById('collectionsGrid');
        const loading = document.getElementById('collectionsLoading');
        
        loading.style.display = 'none';
        
        if (results.length === 0) {
            grid.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search fa-3x"></i>
                    <h3>لا توجد نتائج</h3>
                    <p>لم يتم العثور على نتائج لبحثك.</p>
                </div>
            `;
            return;
        }
        
        // Render search results
        // Similar to renderCollections but with search highlights
    }
    
    async loadCategories() {
        try {
            const response = await fetch(`${this.apiBase}/collections`);
            const data = await response.json();
            
            if (data.success) {
                const categories = new Set();
                data.data.forEach(col => {
                    if (col.category) categories.add(col.category);
                });
                
                const select = document.getElementById('categoryFilter');
                categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }
    
    previewItem(itemId) {
        // Implement item preview modal
        alert(`Preview item ${itemId} - Implement this functionality`);
    }
}

// Initialize app
const app = new StarGiftsApp();
