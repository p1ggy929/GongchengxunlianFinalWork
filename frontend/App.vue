<template>
  <div class="app-container">
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-lg">
      <div class="container-fluid">
        <h1 class="navbar-brand">宫颈细胞学AI辅助诊断系统</h1>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav ms-auto">
            <li class="nav-item">
              <a class="nav-link active" href="#">首页</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="#about">关于系统</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="container my-5">
      <div class="row">
        <!-- 左侧上传区域 -->
        <div class="col-md-6">
          <div class="card shadow-sm">
            <div class="card-header bg-white border-bottom-0">
              <h3 class="card-title text-center mb-0">图像上传</h3>
            </div>
            <div class="card-body">
              <!-- 文件上传区域 -->
              <div 
                class="upload-area mb-4 p-5 text-center border-2 border-dashed rounded-lg cursor-pointer" 
                :class="{ 'border-success': isDragging, 'border-gray-300': !isDragging }"
                @dragover.prevent="onDragOver"
                @dragleave.prevent="onDragLeave"
                @drop.prevent="onDrop"
                @click="triggerFileInput"
              >
                <input 
                  type="file" 
                  ref="fileInput" 
                  class="d-none" 
                  accept="image/*"
                  @change="onFileSelected"
                >
                <svg v-if="!previewImage" class="bi bi-cloud-upload display-4 text-gray-400 mx-auto mb-2" width="64" height="64" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path fill-rule="evenodd" d="M4.406 1.342A5.53 5.53 0 0 1 8 0c2.69 0 4.923 2 5.166 4.579C14.758 4.804 16 6.137 16 7.773 16 9.569 14.502 11 12.687 11H10a.5.5 0 0 1 0-1h2.688C13.979 10 15 8.988 15 7.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 2.825 10.328 1 8 1a4.53 4.53 0 0 0-2.941 1.1c-.757.652-1.153 1.438-1.153 2.055v.448l-.445.049C2.064 4.805 1 5.952 1 7.318 1 8.785 2.23 10 3.781 10H6a.5.5 0 0 1 0 1H3.781C1.708 11 0 9.366 0 7.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383z" clip-rule="evenodd"/>
                  <path fill-rule="evenodd" d="M7.646 4.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 5.707V14.5a.5.5 0 0 1-1 0V5.707L5.354 7.854a.5.5 0 1 1-.708-.708l3-3z" clip-rule="evenodd"/>
                </svg>
                <img v-else :src="previewImage" class="img-fluid rounded mb-2" alt="上传预览">
                <p class="mb-0">{{ previewImage ? '点击或拖拽替换图片' : '点击或拖拽上传图片' }}</p>
              </div>
              
              <!-- 操作按钮 -->
              <div class="d-grid gap-2">
                <button 
                  class="btn btn-primary btn-lg"
                  :disabled="!previewImage || isProcessing"
                  @click="startDiagnosis"
                >
                  <span v-if="isProcessing" class="spinner-border spinner-border-sm me-2"></span>
                  {{ isProcessing ? '诊断中...' : '开始AI诊断' }}
                </button>
                <button 
                  class="btn btn-outline-secondary"
                  :disabled="!previewImage"
                  @click="resetUpload"
                >
                  清除图片
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧结果区域 -->
        <div class="col-md-6">
          <div class="card shadow-sm h-100">
            <div class="card-header bg-white border-bottom-0">
              <h3 class="card-title text-center mb-0">诊断结果</h3>
            </div>
            <div class="card-body">
              <!-- 初始提示 -->
              <div v-if="!isProcessing && !hasError && !diagnosticResult" class="text-center text-gray-500">
                <svg class="bi bi-search display-4 mx-auto mb-2" width="64" height="64" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path fill-rule="evenodd" d="M10.442 10.442a1 1 0 0 1 1.415 0l3.85 3.85a1 1 0 0 1-1.414 1.415l-3.85-3.85a1 1 0 0 1 0-1.415z" clip-rule="evenodd"/>
                  <path fill-rule="evenodd" d="M6.5 12a5.5 5.5 0 1 0 0-11 5.5 5.5 0 0 0 0 11zM13 6.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0z" clip-rule="evenodd"/>
                </svg>
                <p>上传图片后点击「开始AI诊断」按钮查看结果</p>
              </div>

              <!-- 加载状态 -->
              <div v-else-if="isProcessing" class="text-center">
                <div class="spinner-border text-primary mb-4" style="width: 64px; height: 64px;"></div>
                <p>正在进行AI分析，请稍候...</p>
              </div>

              <!-- 错误信息 -->
              <div v-else-if="hasError" class="alert alert-danger">
                <h4 class="alert-heading">分析出错</h4>
                <p>{{ errorMessage }}</p>
                <hr>
                <p class="mb-0">请确保图片清晰可见，并尝试重新上传和分析。</p>
              </div>

              <!-- 诊断结果 -->
              <div v-else-if="diagnosticResult" class="result-container">
                <!-- 总体诊断结果 -->
                <div class="mb-4">
                  <h4 class="mb-2">诊断类别：</h4>
                  <div 
                    class="result-badge d-inline-block px-4 py-2 rounded-full text-white text-lg font-bold"
                    :class="{
                      'bg-green-500': diagnosticResult.category === '正常',
                      'bg-yellow-500': diagnosticResult.category === '轻度异常',
                      'bg-orange-500': diagnosticResult.category === '中度异常',
                      'bg-red-500': diagnosticResult.category === '重度异常'
                    }"
                  >
                    {{ diagnosticResult.category }}
                  </div>
                </div>

                <!-- 置信度分布 -->
                <div class="mb-4">
                  <h4 class="mb-2">细胞类型分析：</h4>
                  <div v-for="(confidence, type) in diagnosticResult.confidence" :key="type" class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                      <span>{{ getCellTypeName(type) }}</span>
                      <span class="font-weight-bold">{{ Math.round(confidence * 100) }}%</span>
                    </div>
                    <div class="progress">
                      <div 
                        class="progress-bar" 
                        role="progressbar"
                        :style="{ width: Math.round(confidence * 100) + '%' }"
                        :class="getProgressBarClass(type)"
                      ></div>
                    </div>
                  </div>
                </div>

                <!-- 诊断建议 -->
                <div class="mb-4">
                  <h4 class="mb-2">医学建议：</h4>
                  <div class="p-3 bg-gray-50 border rounded">
                    <p>{{ diagnosticResult.suggestion }}</p>
                  </div>
                </div>

                <!-- 病变定位信息 -->
                <div v-if="diagnosticResult.lesions && diagnosticResult.lesions.length > 0" class="mb-4">
                  <h4 class="mb-2">病变区域检测：</h4>
                  <div class="p-3 bg-gray-50 border rounded">
                    <p v-if="diagnosticResult.lesions.length === 1">检测到1处可疑病变区域</p>
                    <p v-else>检测到{{ diagnosticResult.lesions.length }}处可疑病变区域</p>
                    <ul class="list-unstyled mt-2">
                      <li v-for="(lesion, index) in diagnosticResult.lesions" :key="index" class="mb-1">
                        区域 {{ index + 1 }}: 位置({{ lesion.x }}, {{ lesion.y }}), 大小 {{ lesion.width }}×{{ lesion.height }}px
                      </li>
                    </ul>
                  </div>
                </div>

                <!-- 原始结果数据 -->
                <div class="mt-4">
                  <details>
                    <summary class="text-muted cursor-pointer">查看详细数据</summary>
                    <pre class="mt-2 p-3 bg-gray-50 rounded overflow-auto text-sm">{{ JSON.stringify(diagnosticResult, null, 2) }}</pre>
                  </details>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统介绍区域 -->
      <section id="about" class="my-8">
        <div class="card">
          <div class="card-header bg-light">
            <h3 class="card-title text-center mb-0">系统介绍</h3>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-4 mb-4">
                <h4 class="text-primary mb-2">技术特点</h4>
                <ul class="list-unstyled">
                  <li class="mb-1">? 基于深度学习的图像识别技术</li>
                  <li class="mb-1">? 集成OpenCV图像预处理</li>
                  <li class="mb-1">? Ascend加速推理引擎</li>
                  <li class="mb-1">? 多类别细胞自动分类</li>
                  <li class="mb-1">? 病变区域智能定位</li>
                </ul>
              </div>
              <div class="col-md-4 mb-4">
                <h4 class="text-primary mb-2">诊断指标</h4>
                <ul class="list-unstyled">
                  <li class="mb-1">? 正常细胞识别</li>
                  <li class="mb-1">? 炎症细胞检测</li>
                  <li class="mb-1">? 不典型鳞状细胞(ASC-US/HSIL)</li>
                  <li class="mb-1">? 癌细胞筛查</li>
                  <li class="mb-1">? 多类别置信度评估</li>
                </ul>
              </div>
              <div class="col-md-4 mb-4">
                <h4 class="text-primary mb-2">适用人群</h4>
                <ul class="list-unstyled">
                  <li class="mb-1">? 宫颈筛查常规体检</li>
                  <li class="mb-1">? 妇科疾病初筛</li>
                  <li class="mb-1">? 高风险人群监测</li>
                  <li class="mb-1">? 宫颈癌早期筛查</li>
                  <li class="mb-1">? 基层医疗机构辅助诊断</li>
                </ul>
              </div>
            </div>
            <div class="alert alert-info mt-4">
              <h5 class="alert-heading">重要提示</h5>
              <p class="mb-0">本系统仅作为辅助诊断工具，所有结果需由专业医师进行最终判断和解释。如有疑问，请咨询相关专科医生。</p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 页脚 -->
    <footer class="bg-gray-800 text-white py-4">
      <div class="container text-center">
        <p class="mb-0">? {{ currentYear }} 宫颈细胞学AI辅助诊断系统 - 医护端</p>
        <p class="text-gray-400 text-sm">本系统仅供医疗专业人员使用</p>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      isDragging: false,
      isProcessing: false,
      hasError: false,
      errorMessage: '',
      previewImage: null,
      selectedFile: null,
      diagnosticResult: null,
      fileInput: null
    }
  },
  computed: {
    currentYear() {
      return new Date().getFullYear()
    }
  },
  methods: {
    // 触发文件选择对话框
    triggerFileInput() {
      this.$refs.fileInput.click()
    },
    
    // 拖拽事件处理
    onDragOver() {
      this.isDragging = true
    },
    
    onDragLeave() {
      this.isDragging = false
    },
    
    onDrop(event) {
      this.isDragging = false
      const files = event.dataTransfer.files
      if (files && files.length > 0) {
        this.handleFile(files[0])
      }
    },
    
    // 文件选择事件处理
    onFileSelected(event) {
      const files = event.target.files
      if (files && files.length > 0) {
        this.handleFile(files[0])
      }
    },
    
    // 处理选中的文件
    handleFile(file) {
      // 验证文件类型
      if (!file.type.startsWith('image/')) {
        this.showError('请上传图片文件')
        return
      }
      
      // 验证文件大小 (限制为10MB)
      if (file.size > 10 * 1024 * 1024) {
        this.showError('图片大小不能超过10MB')
        return
      }
      
      // 重置错误状态
      this.hasError = false
      this.errorMessage = ''
      this.diagnosticResult = null
      
      // 保存文件引用
      this.selectedFile = file
      
      // 创建预览图片URL
      const reader = new FileReader()
      reader.onload = (e) => {
        this.previewImage = e.target.result
      }
      reader.readAsDataURL(file)
    },
    
    // 开始诊断
    async startDiagnosis() {
      if (!this.selectedFile) return
      
      this.isProcessing = true
      this.hasError = false
      this.errorMessage = ''
      
      try {
        // 创建FormData
        const formData = new FormData()
        formData.append('image', this.selectedFile)
        
        // 发送请求到后端API
        const response = await axios.post('/api/diagnose', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 60000 // 60秒超时
        })
        
        // 处理响应结果
        this.diagnosticResult = response.data
        
      } catch (error) {
        console.error('Diagnosis error:', error)
        this.showError(error.response?.data?.error || '诊断过程中发生错误，请重试')
      } finally {
        this.isProcessing = false
      }
    },
    
    // 重置上传
    resetUpload() {
      this.selectedFile = null
      this.previewImage = null
      this.diagnosticResult = null
      this.hasError = false
      this.errorMessage = ''
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    
    // 显示错误
    showError(message) {
      this.hasError = true
      this.errorMessage = message
      this.isProcessing = false
    },
    
    // 获取细胞类型中文名称
    getCellTypeName(type) {
      const typeNames = {
        'normal': '正常细胞',
        'inflammation': '炎症细胞',
        'ascus': '不典型鳞状细胞(ASC-US)',
        'lsil': '低度鳞状上皮内病变(LSIL)',
        'hsil': '高度鳞状上皮内病变(HSIL)',
        'scc': '鳞状细胞癌(SCC)'
      }
      return typeNames[type] || type
    },
    
    // 获取进度条样式类
    getProgressBarClass(type) {
      const classMap = {
        'normal': 'bg-success',
        'inflammation': 'bg-blue-500',
        'ascus': 'bg-yellow-500',
        'lsil': 'bg-orange-500',
        'hsil': 'bg-red-500',
        'scc': 'bg-purple-500'
      }
      return classMap[type] || 'bg-gray-500'
    }
  }
}
</script>

<style>
/* 自定义全局样式 */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

/* 上传区域动画 */
.upload-area {
  transition: all 0.3s ease;
}

.upload-area:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

/* 进度条颜色扩展 */
.bg-blue-500 {
  background-color: #3b82f6;
}

.bg-green-500 {
  background-color: #10b981;
}

.bg-yellow-500 {
  background-color: #f59e0b;
}

.bg-orange-500 {
  background-color: #f97316;
}

.bg-red-500 {
  background-color: #ef4444;
}

.bg-purple-500 {
  background-color: #8b5cf6;
}

/* 平滑过渡效果 */
.result-container > * {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .col-md-6 {
    margin-bottom: 1.5rem;
  }
}
</style>