// �򵥵ļ�������ʵ�� - Ϊ�˼���Vue���ļ�������
function computed(fn) {
    return {
        get: fn
    };
}

// ��ʷ��¼ģ����ط���
function initHistoryModule(vueInstance) {
    // ��ʷ��¼�������
    vueInstance.searchKeyword = '';
    vueInstance.filterType = 'all';
    vueInstance.sortOrder = 'desc';
    vueInstance.currentPage = 1;
    vueInstance.itemsPerPage = 10;
    
    // ������˺����ʷ��¼ - ��ӿ�ֵ���
    vueInstance.filteredHistory = computed(() => {
        let filtered = [...(vueInstance.diagnosticHistory || [])];
        
        // ��������
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
          
          // ���͹���
        if (vueInstance.filterType !== 'all') {
            filtered = filtered.filter(item => 
                item && item.result && item.result.cell_type && 
                item.result.cell_type.toLowerCase() === vueInstance.filterType.toLowerCase()
            );
        }
        
        // ����
        filtered.sort((a, b) => {
            if (!a || !b || !a.timestamp || !b.timestamp) return 0;
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            return vueInstance.sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });
        
        // ��ҳ
        const startIndex = (vueInstance.currentPage - 1) * vueInstance.itemsPerPage;
        return filtered.slice(startIndex, startIndex + vueInstance.itemsPerPage);
    });
    
    // ��ҳ�� - ��ӿ�ֵ���
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
    
    // �ɼ�ҳ��
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
    
    // �鿴��ͼ
    vueInstance.viewLargeImage = function(imageUrl) {
        // ʵ��ͼƬԤ������
        if (imageUrl) {
            // ����ģ̬����ʾ��ͼ
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
                            <img src="${imageUrl}" class="img-fluid" alt="�Ŵ�ͼ��">
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // ��ӹر��¼�
            modal.querySelector('.close').addEventListener('click', () => {
                modal.style.display = 'none';
                document.body.removeChild(modal);
            });
        }
    };
    
    // ������ʷ��¼�����ش洢
    vueInstance.saveHistoryToStorage = function() {
        if (typeof localStorage !== 'undefined') {
            try {
                localStorage.setItem('diagnosticHistory', JSON.stringify(vueInstance.diagnosticHistory));
            } catch (e) {
                console.error('������ʷ��¼ʧ��:', e);
            }
        }
    };
    
    // �ӱ��ش洢������ʷ��¼
    vueInstance.loadHistoryFromStorage = function() {
        if (typeof localStorage !== 'undefined') {
            try {
                const stored = localStorage.getItem('diagnosticHistory');
                if (stored) {
                    vueInstance.diagnosticHistory = JSON.parse(stored);
                }
            } catch (e) {
                console.error('������ʷ��¼ʧ��:', e);
                vueInstance.diagnosticHistory = [];
            }
        }
    };
    
    // ������ʷ��¼
    if (!vueInstance.diagnosticHistory) {
        vueInstance.diagnosticHistory = [];
    }
    vueInstance.loadHistoryFromStorage();
    
    // ���ģ���������ڲ��� - ʹ������SVG�����ⲿ��Դ����
    if (vueInstance.diagnosticHistory.length === 0) {
        vueInstance.diagnosticHistory = [
            {
                fileName: '����ͿƬ_001.jpg',
                timestamp: new Date(Date.now() - 86400000).toISOString(),
                imageUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%23e8f5e9" /%3E%3Ctext x="40" y="45" font-family="Arial" font-size="14" text-anchor="middle" fill="%232e7d32"%3E����%3C/text%3E%3C/svg%3E',
                result: {
                    cell_type: '����',
                    confidence: 0.95,
                    suggestion: 'ϸ��ѧ���δ�������쳣ϸ�������鰴�ճ���ɸ��ƻ����ж��ڸ��顣'
                }
            },
            {
                fileName: '����ͿƬ_002.jpg',
                timestamp: new Date(Date.now() - 172800000).toISOString(),
                imageUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%2fffecb" /%3E%3Ctext x="40" y="45" font-family="Arial" font-size="14" text-anchor="middle" fill="%2fef6c00"%3EASC-US%3C/text%3E%3C/svg%3E',
                result: {
                    cell_type: 'ASC-US',
                    confidence: 0.88,
                    suggestion: '���ֲ�������״ϸ����������и�Σ��HPV��⡣'
                }
            },
            {
                fileName: '����ͿƬ_003.jpg',
                timestamp: new Date(Date.now() - 259200000).toISOString(),
                imageUrl: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80"%3E%3Crect width="80" height="80" fill="%2fffcc8" /%3E%3Ctext x="40" y="45" font-family="Arial" font-size="14" text-anchor="middle" fill="%2fef6c00"%3ELSIL%3C/text%3E%3C/svg%3E',
                result: {
                    cell_type: 'LSIL',
                    confidence: 0.92,
                    suggestion: '��ʾ�Ͷ���״��Ƥ�ڲ��䣬��HPV��Ⱦ��ء����������������顣'
                }
            }
        ];
        vueInstance.saveHistoryToStorage();
    }
    
    // ���������ʷ��¼
    vueInstance.clearAllHistory = function() {
        if (confirm('ȷ��Ҫ���������ʷ��¼�𣿴˲������ɻָ���')) {
            vueInstance.diagnosticHistory = [];
            vueInstance.saveHistoryToStorage();
            vueInstance.currentPage = 1;
            // ����������Ⱦ
            setTimeout(() => {
                const event = new Event('input', { bubbles: true });
                const searchInput = document.getElementById('history-search');
                if (searchInput) searchInput.dispatchEvent(event);
            }, 0);
        }
    };
}

// ͳ�Ʒ���ģ����ط���
function initStatisticsModule(vueInstance) {
    // ͳ���������
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
        { value: '7', label: '���7��' },
        { value: '30', label: '���30��' },
        { value: '90', label: '���90��' },
        { value: 'all', label: 'ȫ��' }
    ];
    
    vueInstance.selectedPeriod = '30';
    vueInstance.distributionLegend = [];
    
    // ͼ��ʵ��
    vueInstance.charts = {
        distribution: null,
        trend: null,
        confidence: null,
        daily: null
    };
    
    // �ı�ʱ�䷶Χ
    vueInstance.changeTimePeriod = function(period) {
        vueInstance.selectedPeriod = period;
        vueInstance.updateStatistics();
        vueInstance.initCharts();
    };
    
    // ����ͳ������
    vueInstance.updateStatistics = function() {
        const history = vueInstance.diagnosticHistory;
        const now = new Date();
        const days = vueInstance.selectedPeriod === 'all' ? 365 * 10 : parseInt(vueInstance.selectedPeriod);
        const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
        
        // ����ָ��ʱ�䷶Χ�ڵļ�¼
        const filteredHistory = history.filter(item => {
            const itemDate = new Date(item.timestamp);
            return itemDate >= cutoffDate;
        });
        
        // ����ͳ������
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
            totalChange: 0, // ���Ը�����ʷ���ݼ���仯��
            confidenceChange: 0
        };
        
        // ׼��ͼ������
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
    
    // ����ͳ�Ʊ���
    vueInstance.exportStatistics = function() {
        // ʹ��jsPDF����PDF����
        if (typeof jsPDF !== 'undefined') {
            const doc = new jsPDF();
            
            // ��ӱ���
            doc.setFontSize(18);
            doc.text('���ͳ�Ʊ���', 20, 20);
            
            // ���ͳ�Ƹ���
            doc.setFontSize(12);
            doc.text(`ͳ��ʱ�䷶Χ: ${vueInstance.timePeriods.find(p => p.value === vueInstance.selectedPeriod)?.label}`, 20, 35);
            doc.text(`����ϴ���: ${vueInstance.statistics.totalDiagnoses}`, 20, 45);
            doc.text(`����ϸ����: ${vueInstance.statistics.normalCount} (${vueInstance.statistics.normalRate}%)`, 20, 55);
            doc.text(`�쳣ϸ����: ${vueInstance.statistics.abnormalCount} (${vueInstance.statistics.abnormalRate}%)`, 20, 65);
            doc.text(`�����Ŷ���: ${vueInstance.statistics.highConfidenceRate}%`, 20, 75);
            
            // �����������
            doc.setFontSize(10);
            doc.text(`��������: ${new Date().toLocaleString()}`, 20, doc.internal.pageSize.height - 10);
            
            // ����PDF
            doc.save(`���ͳ�Ʊ���_${new Date().toISOString().split('T')[0]}.pdf`);
        } else {
            alert('PDF�������ܲ����ã���ȷ���Ѽ���jsPDF�⡣');
        }
    };
    
    // ��ʼ��ͼ��
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
        // ����ģ����������
        const labels = [];
        const data = [];
        const now = new Date();
        const days = vueInstance.selectedPeriod === 'all' ? 30 : Math.min(parseInt(vueInstance.selectedPeriod), 30);
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }));
            data.push(Math.floor(Math.random() * 20) + 5); // ģ������
        }
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'ÿ�������',
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

// ��ʼ������ģ��
function initModules(vueInstance) {
    // ��ʼ����ʷ��¼ģ��
    initHistoryModule(vueInstance);
    
    // ��ʼ��ͳ�Ʒ���ģ��
    initStatisticsModule(vueInstance);
    
    // ��ʼ����ǩҳ�л��¼�����
    initTabNavigation(vueInstance);
}

// ��ʼ����ǩҳ����
function initTabNavigation(vueInstance) {
    // Ϊ���б�ǩҳ������ӵ���¼�
    document.querySelectorAll('.nav-link[data-tab]').forEach(link => {
        link.addEventListener('click', function(e) {
            // ������±�ǩҳ�򿪣�������
            if (this.getAttribute('target') === '_blank') {
                return;
            }
            
            e.preventDefault();
            const moduleName = this.getAttribute('data-tab');
            
            // �����SPAģʽ����ͨ��API��������
            if (window.useSPAMode) {
                loadModuleContent(moduleName, 'tab-content-container', vueInstance);
                
                // ����URL����ˢ��ҳ��
                history.pushState({module: moduleName}, '', `/${moduleName}`);
            } else {
                // �������ҳ����ת
                window.location.href = `/${moduleName}`;
            }
        });
    });
    
    // ���������ǰ�����˰�ť
    window.addEventListener('popstate', function(e) {
        if (window.useSPAMode && e.state && e.state.module) {
            loadModuleContent(e.state.module, 'tab-content-container', vueInstance);
        }
    });
}

// ����ģ�����ݺ���
function loadModuleContent(moduleName, containerId, vueInstance) {
    const container = document.getElementById(containerId);
    
    // ��ʾ������״̬
    container.innerHTML = `<div class="text-center py-5"><i class="fa fa-spinner fa-spin fa-3x text-primary"></i><p class="mt-2">������...</p></div>`;
    
    // ���ʱ��������Է�ֹ����
    const timestamp = new Date().getTime();
    
    // ֱ�Ӽ���HTML�ļ�����ӻ������
    fetch(`/modules/${moduleName}.html?t=${timestamp}`, {
        headers: {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('������Ӧ�쳣');
            }
            return response.text();
        })
        .then(html => {
            container.innerHTML = html;
            
            // ����ģ�����Ƴ�ʼ����Ӧ����
            if (moduleName === 'history') {
                initHistoryModule(vueInstance);
            } else if (moduleName === 'statistics') {
                initStatisticsModule(vueInstance);
            }
        })
        .catch(error => {
            console.error(`����${moduleName}ģ��ʧ��:`, error);
            container.innerHTML = `<div class="alert alert-danger">����${moduleName}ģ��ʧ�ܣ���ˢ��ҳ������</div>`;
        });
}

// �����Ƿ�ʹ��SPAģʽ
window.useSPAMode = true;

// ����URL·�������Ӧ��ǩҳ
function activateTabByURL(vueInstance) {
    const path = window.location.pathname;
    let targetTab = 'diagnosis'; // Ĭ�ϼ�����Ϸ�����ǩ
    
    // ����URL·��ȷ��Ŀ���ǩ
    if (path.includes('/history')) {
        targetTab = 'history';
    } else if (path.includes('/statistics')) {
        targetTab = 'statistics';
    } else if (path.includes('/about')) {
        targetTab = 'about';
    }
    
    // ����historyҳ�����⴦��ȷ�����¼���ʱ����ȷ��Ⱦ
    if (targetTab === 'history' && window.useSPAMode) {
        // �������������ֹ�����ݸ���
        const container = document.getElementById('tab-content-container');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    // �����SPAģʽ�Ҳ���Ĭ��ҳ�棬����ض�Ӧģ������
    if (window.useSPAMode && targetTab !== 'diagnosis' && path !== '/') {
        // �ȸ���URL״̬��ȷ��ǰ�����˹�������
        history.replaceState({module: targetTab}, '', `/${targetTab}`);
        
        // Ȼ�����ģ������
        loadModuleContent(targetTab, 'tab-content-container', vueInstance);
    } else if (targetTab === 'diagnosis') {
        // ��������ҳ�棬���������VueӦ��������ʾ
        const container = document.getElementById('tab-content-container');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    // ���±�ǩҳ����״̬
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

// ҳ�������ɺ��ʼ����������
document.addEventListener('DOMContentLoaded', function() {
    // ����Ƿ����VueӦ��ʵ��
    let vueInstance;
    
    if (window.cervicalApp) {
        vueInstance = window.cervicalApp;
    } else {
        // ���û��Vueʵ��������һ���򵥵Ķ�����Ϊ���
        vueInstance = {
            diagnosticHistory: [],
            searchKeyword: '',
            filterType: 'all',
            sortOrder: 'desc',
            currentPage: 1,
            itemsPerPage: 10
        };
    }
    
    // ��ʼ������
    initTabNavigation(vueInstance);
    
    // ����URL�����Ӧ��ǩҳ
    activateTabByURL(vueInstance);
});