// Mock数据服务，用于演示应用功能

export class MockDataService {
  // 模拟诊断结果
  static async mockDiagnose(): Promise<any> {
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 随机生成诊断结果
    const cellTypes = ['正常', 'ASC-US', 'LSIL', 'HSIL'];
    const randomIndex = Math.floor(Math.random() * cellTypes.length);
    const confidence = 0.65 + Math.random() * 0.3;
    
    return {
      cell_type: cellTypes[randomIndex],
      class_index: randomIndex,
      confidence: confidence,
      timestamp: new Date().toISOString(),
      // 添加更多模拟数据
      analysis_details: {
        cell_count: Math.floor(Math.random() * 50) + 20,
        abnormal_cell_count: randomIndex > 0 ? Math.floor(Math.random() * 10) + 1 : 0,
        recommended_follow_up: this.getRecommendedFollowUp(randomIndex, confidence)
      }
    };
  }
  
  // 获取推荐随访方案
  private static getRecommendedFollowUp(classIndex: number, confidence: number): string {
    const recommendations = [
      '建议12个月后复查宫颈细胞学。',
      '建议3-6个月后重复宫颈细胞学检查，并考虑HPV检测。',
      '建议转诊进行阴道镜检查和宫颈活检。',
      '建议立即转诊进行阴道镜检查和宫颈活检评估。'
    ];
    
    return recommendations[classIndex] || '请咨询专业医生获取个性化建议。';
  }
  
  // 检查是否使用Mock模式
  static isMockMode(): boolean {
    // 可以通过配置或环境变量来控制是否启用Mock模式
    return true;
  }
}