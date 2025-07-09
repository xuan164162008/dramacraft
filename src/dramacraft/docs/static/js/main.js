/**
 * DramaCraft 文档系统主要JavaScript文件
 * 提供交互功能和用户体验优化
 */

// 全局状态管理
const DocumentationApp = {
    state: {
        currentTheme: 'light',
        currentLanguage: 'zh',
        sidebarOpen: true,
        searchResults: [],
        activeSection: null
    },
    
    // 初始化应用
    init() {
        this.initializeTheme();
        this.initializeLanguage();
        this.initializeNavigation();
        this.initializeSearch();
        this.initializeCodeBlocks();
        this.initializeScrollSpy();
        this.initializeTOC();
        this.bindEvents();
    },
    
    // 初始化主题
    initializeTheme() {
        const savedTheme = localStorage.getItem('dramacraft-theme') || 'light';
        this.setTheme(savedTheme);
    },
    
    // 设置主题
    setTheme(theme) {
        this.state.currentTheme = theme;
        document.body.className = `theme-${theme}`;
        localStorage.setItem('dramacraft-theme', theme);
        
        // 更新主题切换按钮
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const lightIcon = themeToggle.querySelector('.theme-icon-light');
            const darkIcon = themeToggle.querySelector('.theme-icon-dark');
            
            if (theme === 'dark') {
                lightIcon.style.display = 'none';
                darkIcon.style.display = 'block';
            } else {
                lightIcon.style.display = 'block';
                darkIcon.style.display = 'none';
            }
        }
    },
    
    // 切换主题
    toggleTheme() {
        const newTheme = this.state.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    },
    
    // 初始化语言
    initializeLanguage() {
        const savedLanguage = localStorage.getItem('dramacraft-language') || 'zh';
        this.setLanguage(savedLanguage);
    },
    
    // 设置语言
    setLanguage(language) {
        this.state.currentLanguage = language;
        localStorage.setItem('dramacraft-language', language);
        
        // 更新语言按钮文本
        const languageBtn = document.getElementById('language-btn');
        if (languageBtn) {
            const languageText = languageBtn.querySelector('.language-text');
            languageText.textContent = language === 'zh' ? '中文' : 'English';
        }
        
        // 这里可以添加实际的语言切换逻辑
        this.loadLanguageContent(language);
    },
    
    // 加载语言内容
    async loadLanguageContent(language) {
        try {
            // 模拟加载语言文件
            console.log(`Loading language: ${language}`);
            // 实际实现中，这里会加载对应的语言文件
        } catch (error) {
            console.error('Failed to load language content:', error);
        }
    },
    
    // 初始化导航
    initializeNavigation() {
        // 高亮当前页面的导航项
        const currentPath = window.location.hash || '#overview';
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            }
        });
    },
    
    // 初始化搜索功能
    initializeSearch() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        
        if (searchInput && searchResults) {
            let searchTimeout;
            
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length < 2) {
                    this.hideSearchResults();
                    return;
                }
                
                searchTimeout = setTimeout(() => {
                    this.performSearch(query);
                }, 300);
            });
            
            // 点击外部关闭搜索结果
            document.addEventListener('click', (e) => {
                if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                    this.hideSearchResults();
                }
            });
        }
    },
    
    // 执行搜索
    async performSearch(query) {
        try {
            // 加载搜索索引
            const response = await fetch('search.json');
            const searchIndex = await response.json();
            
            // 执行搜索
            const results = this.searchInIndex(query, searchIndex);
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search failed:', error);
        }
    },
    
    // 在索引中搜索
    searchInIndex(query, searchIndex) {
        const queryWords = query.toLowerCase().split(' ');
        const results = [];
        const scoreMap = new Map();
        
        // 计算每个文档的相关性分数
        queryWords.forEach(word => {
            if (searchIndex.index[word]) {
                searchIndex.index[word].forEach(docId => {
                    const currentScore = scoreMap.get(docId) || 0;
                    scoreMap.set(docId, currentScore + 1);
                });
            }
        });
        
        // 获取匹配的文档并按分数排序
        scoreMap.forEach((score, docId) => {
            const doc = searchIndex.documents.find(d => d.id === docId);
            if (doc) {
                results.push({
                    ...doc,
                    score
                });
            }
        });
        
        return results.sort((a, b) => b.score - a.score).slice(0, 10);
    },
    
    // 显示搜索结果
    displaySearchResults(results) {
        const searchResults = document.getElementById('search-results');
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-no-results">未找到相关结果</div>';
        } else {
            const resultsHTML = results.map(result => `
                <a href="${result.url}" class="search-result-item">
                    <div class="search-result-title">${result.title}</div>
                    <div class="search-result-content">${this.truncateText(result.content, 100)}</div>
                </a>
            `).join('');
            
            searchResults.innerHTML = resultsHTML;
        }
        
        searchResults.style.display = 'block';
    },
    
    // 隐藏搜索结果
    hideSearchResults() {
        const searchResults = document.getElementById('search-results');
        if (searchResults) {
            searchResults.style.display = 'none';
        }
    },
    
    // 截断文本
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },
    
    // 初始化代码块
    initializeCodeBlocks() {
        // 添加复制按钮到代码块
        const codeBlocks = document.querySelectorAll('.code-block');
        
        codeBlocks.forEach(block => {
            const copyBtn = block.querySelector('.copy-code-btn');
            if (copyBtn) {
                copyBtn.addEventListener('click', () => {
                    const code = copyBtn.getAttribute('data-code');
                    this.copyToClipboard(code);
                    this.showCopyFeedback(copyBtn);
                });
            }
        });
        
        // 初始化可运行示例
        const runButtons = document.querySelectorAll('.run-example-btn');
        runButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const exampleId = e.target.getAttribute('data-example-id');
                this.runExample(exampleId);
            });
        });
    },
    
    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
        } catch (error) {
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        }
    },
    
    // 显示复制反馈
    showCopyFeedback(button) {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        button.style.background = 'var(--success-color)';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
        }, 2000);
    },
    
    // 运行示例
    async runExample(exampleId) {
        try {
            // 这里实现代码示例的运行逻辑
            console.log(`Running example ${exampleId}`);
            
            // 模拟API调用
            const response = await fetch('/api/run-example', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ exampleId })
            });
            
            const result = await response.json();
            this.displayExampleResult(exampleId, result);
        } catch (error) {
            console.error('Failed to run example:', error);
            this.displayExampleError(exampleId, error.message);
        }
    },
    
    // 显示示例结果
    displayExampleResult(exampleId, result) {
        const exampleBlock = document.querySelector(`[data-example-id="${exampleId}"]`).closest('.example-block');
        let outputBlock = exampleBlock.querySelector('.output-block');
        
        if (!outputBlock) {
            outputBlock = document.createElement('div');
            outputBlock.className = 'output-block';
            outputBlock.innerHTML = `
                <div class="output-header">运行结果</div>
                <pre class="output-content"></pre>
            `;
            exampleBlock.appendChild(outputBlock);
        }
        
        const outputContent = outputBlock.querySelector('.output-content');
        outputContent.textContent = JSON.stringify(result, null, 2);
    },
    
    // 显示示例错误
    displayExampleError(exampleId, errorMessage) {
        const exampleBlock = document.querySelector(`[data-example-id="${exampleId}"]`).closest('.example-block');
        let outputBlock = exampleBlock.querySelector('.output-block');
        
        if (!outputBlock) {
            outputBlock = document.createElement('div');
            outputBlock.className = 'output-block error';
            outputBlock.innerHTML = `
                <div class="output-header">运行错误</div>
                <pre class="output-content"></pre>
            `;
            exampleBlock.appendChild(outputBlock);
        }
        
        const outputContent = outputBlock.querySelector('.output-content');
        outputContent.textContent = errorMessage;
    },
    
    // 初始化滚动监听
    initializeScrollSpy() {
        const sections = document.querySelectorAll('.doc-section');
        const navItems = document.querySelectorAll('.nav-item');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const sectionId = entry.target.id;
                    this.updateActiveNavigation(sectionId);
                    this.updateActiveTOC(sectionId);
                }
            });
        }, {
            rootMargin: '-20% 0px -70% 0px'
        });
        
        sections.forEach(section => {
            observer.observe(section);
        });
    },
    
    // 更新活动导航
    updateActiveNavigation(sectionId) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === `#${sectionId}`) {
                item.classList.add('active');
            }
        });
    },
    
    // 更新活动目录
    updateActiveTOC(sectionId) {
        const tocItems = document.querySelectorAll('.toc-nav a');
        tocItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href') === `#${sectionId}`) {
                item.classList.add('active');
            }
        });
    },
    
    // 初始化目录
    initializeTOC() {
        const tocNav = document.getElementById('toc-nav');
        if (!tocNav) return;
        
        const headings = document.querySelectorAll('.content h2, .content h3, .content h4');
        const tocItems = [];
        
        headings.forEach(heading => {
            if (heading.id) {
                const level = parseInt(heading.tagName.charAt(1));
                tocItems.push({
                    id: heading.id,
                    text: heading.textContent,
                    level: level
                });
            }
        });
        
        const tocHTML = tocItems.map(item => `
            <a href="#${item.id}" class="toc-item level-${item.level}">
                ${item.text}
            </a>
        `).join('');
        
        tocNav.innerHTML = tocHTML;
    },
    
    // 绑定事件
    bindEvents() {
        // 主题切换
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // 语言切换
        const languageBtn = document.getElementById('language-btn');
        const languageMenu = document.getElementById('language-menu');
        
        if (languageBtn && languageMenu) {
            languageBtn.addEventListener('click', () => {
                languageMenu.style.display = languageMenu.style.display === 'block' ? 'none' : 'block';
            });
            
            const languageOptions = languageMenu.querySelectorAll('.language-option');
            languageOptions.forEach(option => {
                option.addEventListener('click', (e) => {
                    e.preventDefault();
                    const language = option.getAttribute('data-lang');
                    this.setLanguage(language);
                    languageMenu.style.display = 'none';
                });
            });
        }
        
        // 侧边栏切换
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K 打开搜索
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Escape 关闭搜索结果
            if (e.key === 'Escape') {
                this.hideSearchResults();
            }
        });
    },
    
    // 切换侧边栏
    toggleSidebar() {
        this.state.sidebarOpen = !this.state.sidebarOpen;
        const sidebar = document.querySelector('.sidebar');
        const mainContainer = document.querySelector('.main-container');
        
        if (this.state.sidebarOpen) {
            sidebar.style.display = 'block';
            mainContainer.style.gridTemplateColumns = 'var(--sidebar-width) 1fr var(--toc-width)';
        } else {
            sidebar.style.display = 'none';
            mainContainer.style.gridTemplateColumns = '0 1fr var(--toc-width)';
        }
    }
};

// 初始化文档应用
function initializeDocumentation() {
    DocumentationApp.init();
}

// 导出到全局
window.DocumentationApp = DocumentationApp;
window.initializeDocumentation = initializeDocumentation;
