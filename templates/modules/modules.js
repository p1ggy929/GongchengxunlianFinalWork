// 简单的计算属性实现 - 为了兼容Vue风格的计算属性
function computed(fn) {
    return {
        get: fn
    };
}

// 历史记录模块相关方法
function initHistoryModule(vueInstance) {
    // 历史记录相关数据
    vueInstance.searchKeyword = '';
    vueInstance.filterType = 'all';
    vueInstance.sortOrder = 'desc';
    vueInstance.currentPage = 1;
    vueInstance.itemsPerPage = 10;
    
    // 计算过滤后的历史记录 - 添加空值检查
    vueInstance.filteredHistory = computed(() => {
        let filtered = [...(vueInstance.diagnosticHistory || [])];
        
        // 搜索过滤
        if (vueInstance.searchKeyword) {
            const keyword = vueInstance.searchKeyword.toLowerCase();
            filtered = filtered.filter(item => 
                item && (
                    (item.fileName && item.fileName.toLowerCase().includes(keyword)) ||
                    (item.result && item.result.cell_type && item.result.cell_type.toLowerCase().includes(keyword)) ||
                    (item.result && item.result.suggestion && item.result.suggestion.toLowerCase().includes(keyword))
                )
            );
          }
          
          // 类型过滤
        if (vueInstance.filterType !== 'all') {
            filtered = filtered.filter(item => 
                item && item.result && item.result.cell_type && 
                item.result.cell_type.toLowerCase() === vueInstance.filterType.toLowerCase()
            );
        }
        
        // 排序
        filtered.sort((a, b) => {
            if (!a || !b || !a.timestamp || !b.timestamp) return 0;
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            return vueInstance.sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });
        
        // 分页
        const startIndex = (vueInstance.currentPage - 1) * vueInstance.itemsPerPage;
        return filtered.slice(startIndex, startIndex + vueInstance.itemsPerPage);
    });
    
    // 总页数 - 添加空值检查
    vueInstance.totalPages = computed(() => {
        let filtered = [...(vueInstance.diagnosticHistory || [])];
        
        if (vueInstance.searchKeyword) {
            const keyword = vueInstance.searchKeyword.toLowerCase();
            filtered = filtered.filter(item => 
                item && (
                    (item.fileName && item.fileName.toLowerCase().includes(keyword)) ||
                    (item.result && item.result.cell_type && item.result.cell_type.toLowerCase().includes(keyword)) ||
                    (item.result && item.result.suggestion && item.result.suggestion.toLowerCase().includes(keyword))
                )
            );
        }
        
        if (vueInstance.filterType !== 'all') {
            filtered = filtered.filter(item => 
                item && item.result && item.result.cell_type && 
                item.result.cell_type.toLowerCase() === vueInstance.filterType.toLowerCase()
            );
        }
        
        return Math.ceil(filtered.length / vueInstance.itemsPerPage);
    });
    
    // 可见页码
    vueInstance.visiblePages = computed(() => {
        const pages = [];
        const total = vueInstance.totalPages;
        const current = vueInstance.currentPage;
        
        let start = Math.max(1, current - 2);
        let end = Math.min(total, start + 4);
        
        if (end - start < 4 && start > 1) {
            start = Math.max(1, end - 4);
        }
        
        for (let i = start; i <= end; i++) {
            pages.push(i);
        }
        
        return pages;
    });
    
    // 查看大图
    vueInstance.viewLargeImage = function(imageUrl) {
        // 实现图片预览功能
        if (imageUrl) {
            // 创建模态框显示大图
            const modal = document.createElement('div');
            modal.className = 'modal fade show';
            modal.style.display = 'block';
            modal.style.zIndex = '1050';
            modal.innerHTML = `
                <div class="modal-dialog modal-xl modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <img src="${imageUrl}" class="img-fluid" alt="放大图像">
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 添加关闭事件
            modal.querySelector('.close').addEventListener('click', () => {
                modal.style.display = 'none';
                document.body.removeChild(modal);
            });
        }
    };
    
    // 保存历史记录到本地存储
    vueInstance.saveHistoryToStorage = function() {
        if (typeof localStorage !== 'undefined') {
            try {
                localStorage.setItem('diagnosticHistory', JSON.stringify(vueInstance.diagnosticHistory));
            } catch (e) {
                console.error('保存历史记录失败:', e);
            }
        }
    };
    
    // 从本地存储加载历史记录
    vueInstance.loadHistoryFromStorage = function() {
        if (typeof localStorage !== 'undefined') {
            try {
                const stored = localStorage.getItem('diagnosticHistory');
                if (stored) {
                    vueInstance.diagnosticHistory = JSON.parse(stored);
                }
            } catch (e) {
                console.error('加载历史记录失败:', e);
                vueInstance.diagnosticHistory = [];
            }
        }
    };
    
    // 加载历史记录
    if (!vueInstance.diagnosticHistory) {
        vueInstance.diagnosticHistory = [];
    }
    vueInstance.loadHistoryFromStorage();
    
    // 添加模拟数据用于测试 - 使用内联SVG避免外部资源请求
    if (vueInstance.diagnosticHistory.length === 0) {
        vueInstance.diagnosticHistory = [
            {
                fileName: '宫颈涂片_001.jpg',
                timestamp: new Date(Date.now() - 86400000).toISOString(),
                imageUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%23e8f5e9" /%3E%3Ctext x="40" y="45" font-family="Arial" font-size="14" text-anchor="middle" fill="%232e7d32"%3E正常%3C/text%3E%3C/svg%3E',
                result: {
                    cell_type: '正常',
                    confidence: 0.95,
                    suggestion: '细胞学检查未见明显异常细胞，建议按照常规筛查计划进行定期复查。'
                }
            },
            {
                fileName: '宫颈涂片_002.jpg',
                timestamp: new Date(Date.now() - 172800000).toISOString(),
                imageUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%2fffecb" /%3E%3Ctext x="40" y="45" font-family="Arial" font-size="14" text-anchor="middle" fill="%2fef6c00"%3EASC-US%3C/text%3E%3C/svg%3E',
                result: {
                    cell_type: 'ASC-US',
                    confidence: 0.88,
                    suggestion: '发现不典型鳞状细胞，建议进行高危型HPV检测。'
                }
            },
            {
                fileName: '宫颈涂片_003.jpg',
                timestamp: new Date(Date.now() - 259200000).toISOString(),
                imageUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%2fffcc8" /%3E%3Ctext x="40" y="45" font-family="Arial" font-size="14" text-anchor="middle" fill="%2fef6c00"%3ELSIL%3C/text%3E%3C/svg%3E',
                result: {
                    cell_type: 'LSIL',
                    confidence: 0.92,
                    suggestion: '提示低度鳞状上皮内病变，与HPV感染相关。建议进行阴道镜检查。'
                }
            }
        ];
        vueInstance.saveHistoryToStorage();
    }
    
    // 清空所有历史记录
    vueInstance.clearAllHistory = function() {
        if (confirm('确定要清空所有历史记录吗？此操作不可恢复。')) {
            vueInstance.diagnosticHistory = [];
            vueInstance.saveHistoryToStorage();
            vueInstance.currentPage = 1;
            // 触发重新渲染
            setTimeout(() => {
                const event = new Event('input', { bubbles: true });
                const searchInput = document.getElementById('history-search');
                if (searchInput) searchInput.dispatchEvent(event);
            }, 0);
        }
    };
}

// 统计分析模块相关方法
function initStatisticsModule(vueInstance) {
    // 统计数据相关
    vueInstance.statistics = {
        totalDiagnoses: 0,
        normalCount: 0,
        abnormalCount: 0,
        normalRate: 0,
        abnormalRate: 0,
        highConfidenceRate: 0,
        totalChange: 0,
        confidenceChange: 0
    };
    
    vueInstance.timePeriods = [
        { value: '7', label: '最近7天' },
        { value: '30', label: '最近30天' },
        { value: '90', label: '最近90天' },
        { value: 'all', label: '全部' }
    ];
    
    vueInstance.selectedPeriod = '30';
    vueInstance.distributionLegend = [];
    
    // 图表实例
    vueInstance.charts = {
        distribution: null,
        trend: null,
        confidence: null,
        daily: null
    };
    
    // 改变时间范围
    vueInstance.changeTimePeriod = function(period) {
        vueInstance.selectedPeriod = period;
        vueInstance.updateStatistics();
        vueInstance.initCharts();
    };
    
    // 更新统计数据
    vueInstance.updateStatistics = function() {
        const history = vueInstance.diagnosticHistory;
        const now = new Date();
        const days = vueInstance.selectedPeriod === 'all' ? 365 * 10 : parseInt(vueInstance.selectedPeriod);
        const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
        
        // 过滤指定时间范围内的记录
        const filteredHistory = history.filter(item => {
            const itemDate = new Date(item.timestamp);
            return itemDate >= cutoffDate;
        });
        
        // 计算统计数据
        const total = filteredHistory.length;
        const normalCount = filteredHistory.filter(item => 
            item.result.cell_type.toLowerCase() === 'normal'
        ).length;
        const abnormalCount = total - normalCount;
        
        const highConfidenceCount = filteredHistory.filter(item => 
            item.result.confidence >= 0.8
        ).length;
        
        vueInstance.statistics = {
            totalDiagnoses: total,
            normalCount: normalCount,
            abnormalCount: abnormalCount,
            normalRate: total > 0 ? Math.round((normalCount / total) * 100) : 0,
            abnormalRate: total > 0 ? Math.round((abnormalCount / total) * 100) : 0,
            highConfidenceRate: total > 0 ? Math.round((highConfidenceCount / total) * 100) : 0,
            totalChange: 0, // 可以根据历史数据计算变化率
            confidenceChange: 0
        };
        
        // 准备图例数据
        const typeCounts = {};
        filteredHistory.forEach(item => {
            const type = item.result.cell_type;
            typeCounts[type] = (typeCounts[type] || 0) + 1;
        });
        
        vueInstance.distributionLegend = Object.entries(typeCounts).map(([type, count]) => ({
            label: type,
            value: count,
            color: vueInstance.getResultClass(type, true)
        }));
    };
    
    // 导出统计报告
    vueInstance.exportStatistics = function() {
        // 使用jsPDF导出PDF报告
        if (typeof jsPDF !== 'undefined') {
            const doc = new jsPDF();
            
            // 添加标题
            doc.setFontSize(18);
            doc.text('诊断统计报告', 20, 20);
            
            // 添加统计概览
            doc.setFontSize(12);
            doc.text(`统计时间范围: ${vueInstance.timePeriods.find(p => p.value === vueInstance.selectedPeriod)?.label}`, 20, 35);
            doc.text(`总诊断次数: ${vueInstance.statistics.totalDiagnoses}`, 20, 45);
            doc.text(`正常细胞数: ${vueInstance.statistics.normalCount} (${vueInstance.statistics.normalRate}%)`, 20, 55);
            doc.text(`异常细胞数: ${vueInstance.statistics.abnormalCount} (${vueInstance.statistics.abnormalRate}%)`, 20, 65);
            doc.text(`高置信度率: ${vueInstance.statistics.highConfidenceRate}%`, 20, 75);
            
            // 添加生成日期
            doc.setFontSize(10);
            doc.text(`生成日期: ${new Date().toLocaleString()}`, 20, doc.internal.pageSize.height - 10);
            
            // 保存PDF
            doc.save(`诊断统计报告_${new Date().toISOString().split('T')[0]}.pdf`);
        } else {
            alert('PDF导出功能不可用，请确保已加载jsPDF库。');
        }
    };
    
    // 初始化图表
    vueInstance.createDistributionChart = function(canvas) {
        if (!canvas || typeof Chart === 'undefined') return null;
        
        const ctx = canvas.getContext('2d');
        const labels = vueInstance.distributionLegend.map(item => item.label);
        const data = vueInstance.distributionLegend.map(item => item.value);
        const colors = vueInstance.distributionLegend.map(item => item.color);
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    };
    
    vueInstance.createTrendChart = function(canvas) {
        if (!canvas || typeof Chart === 'undefined') return null;
        
        const ctx = canvas.getContext('2d');
        // 生成模拟趋势数据
        const labels = [];
        const data = [];
        const now = new Date();
        const days = vueInstance.selectedPeriod === 'all' ? 30 : Math.min(parseInt(vueInstance.selectedPeriod), 30);
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }));
            data.push(Math.floor(Math.random() * 20) + 5); // 模拟数据
        }
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '每日诊断量',
                    data: data,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    };
}

// 初始化所有模块
function initModules(vueInstance) {
    // 初始化历史记录模块
    initHistoryModule(vueInstance);
    
    // 初始化统计分析模块
    initStatisticsModule(vueInstance);
    
    // 初始化标签页切换事件监听
    initTabNavigation(vueInstance);
}

// 初始化标签页导航
function initTabNavigation(vueInstance) {
    // 为所有标签页链接添加点击事件
    document.querySelectorAll('.nav-link[data-tab]').forEach(link => {
        link.addEventListener('click', function(e) {
            // 如果是新标签页打开，则不拦截
            if (this.getAttribute('target') === '_blank') {
                return;
            }
            
            e.preventDefault();
            const moduleName = this.getAttribute('data-tab');
            
            // 如果是SPA模式，则通过API加载内容
            if (window.useSPAMode) {
                loadModuleContent(moduleName, 'tab-content-container', vueInstance);
                
                // 更新URL但不刷新页面
                history.pushState({module: moduleName}, '', `/${moduleName}`);
            } else {
                // 否则进行页面跳转
                window.location.href = `/${moduleName}`;
            }
        });
    });
    
    // 处理浏览器前进后退按钮
    window.addEventListener('popstate', function(e) {
        if (window.useSPAMode && e.state && e.state.module) {
            loadModuleContent(e.state.module, 'tab-content-container', vueInstance);
        }
    });
}

// 加载模块内容函数
function loadModuleContent(moduleName, containerId, vueInstance) {
    const container = document.getElementById(containerId);
    
    // 显示加载中状态
    container.innerHTML = `<div class="text-center py-5"><i class="fa fa-spinner fa-spin fa-3x text-primary"></i><p class="mt-2">加载中...</p></div>`;
    
    // 添加时间戳参数以防止缓存
    const timestamp = new Date().getTime();
    
    // 直接加载HTML文件，添加缓存控制
    fetch(`/modules/${moduleName}.html?t=${timestamp}`, {
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.text();
        })
        .then(html => {
            container.innerHTML = html;
            
            // 根据模块名称初始化对应功能
            if (moduleName === 'history') {
                initHistoryModule(vueInstance);
            } else if (moduleName === 'statistics') {
                initStatisticsModule(vueInstance);
            }
        })
        .catch(error => {
            console.error(`加载${moduleName}模块失败:`, error);
            container.innerHTML = `<div class="alert alert-danger">加载${moduleName}模块失败，请刷新页面重试</div>`;
        });
}

// 定义是否使用SPA模式
window.useSPAMode = true;

// 根据URL路径激活对应标签页
function activateTabByURL(vueInstance) {
    const path = window.location.pathname;
    let targetTab = 'diagnosis'; // 默认激活诊断分析标签
    
    // 根据URL路径确定目标标签
    if (path.includes('/history')) {
        targetTab = 'history';
    } else if (path.includes('/statistics')) {
        targetTab = 'statistics';
    } else if (path.includes('/about')) {
        targetTab = 'about';
    }
    
    // 对于history页面特殊处理，确保重新加载时能正确渲染
    if (targetTab === 'history' && window.useSPAMode) {
        // 先清空容器，防止旧内容干扰
        const container = document.getElementById('tab-content-container');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    // 如果是SPA模式且不是默认页面，则加载对应模块内容
    if (window.useSPAMode && targetTab !== 'diagnosis' && path !== '/') {
        // 先更新URL状态，确保前进后退功能正常
        history.replaceState({module: targetTab}, '', `/${targetTab}`);
        
        // 然后加载模块内容
        loadModuleContent(targetTab, 'tab-content-container', vueInstance);
    } else if (targetTab === 'diagnosis') {
        // 如果是诊断页面，清空容器让Vue应用正常显示
        const container = document.getElementById('tab-content-container');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    // 更新标签页激活状态
    document.querySelectorAll('.nav-link[data-tab]').forEach(link => {
        const tabName = link.getAttribute('data-tab');
        if (tabName === targetTab) {
            link.classList.add('active');
            link.setAttribute('aria-selected', 'true');
        } else {
            link.classList.remove('active');
            link.setAttribute('aria-selected', 'false');
        }
    });
}

// 页面加载完成后初始化导航功能
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否存在Vue应用实例
    let vueInstance;
    
    if (window.cervicalApp) {
        vueInstance = window.cervicalApp;
    } else {
        // 如果没有Vue实例，创建一个简单的对象作为替代
        vueInstance = {
            diagnosticHistory: [],
            searchKeyword: '',
            filterType: 'all',
            sortOrder: 'desc',
            currentPage: 1,
            itemsPerPage: 10
        };
    }
    
    // 初始化导航
    initTabNavigation(vueInstance);
    
    // 根据URL激活对应标签页
    activateTabByURL(vueInstance);
});