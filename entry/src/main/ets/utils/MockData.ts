// Mock���ݷ���������ʾӦ�ù���

export class MockDataService {
  // ģ����Ͻ��
  static async mockDiagnose(): Promise<any> {
    // ģ�������ӳ�
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // ���������Ͻ��
    const cellTypes = ['����', 'ASC-US', 'LSIL', 'HSIL'];
    const randomIndex = Math.floor(Math.random() * cellTypes.length);
    const confidence = 0.65 + Math.random() * 0.3;
    
    return {
      cell_type: cellTypes[randomIndex],
      class_index: randomIndex,
      confidence: confidence,
      timestamp: new Date().toISOString(),
      // ��Ӹ���ģ������
      analysis_details: {
        cell_count: Math.floor(Math.random() * 50) + 20,
        abnormal_cell_count: randomIndex > 0 ? Math.floor(Math.random() * 10) + 1 : 0,
        recommended_follow_up: this.getRecommendedFollowUp(randomIndex, confidence)
      }
    };
  }
  
  // ��ȡ�Ƽ���÷���
  private static getRecommendedFollowUp(classIndex: number, confidence: number): string {
    const recommendations = [
      '����12���º󸴲鹬��ϸ��ѧ��',
      '����3-6���º��ظ�����ϸ��ѧ��飬������HPV��⡣',
      '����ת��������������͹�����졣',
      '��������ת��������������͹������������'
    ];
    
    return recommendations[classIndex] || '����ѯרҵҽ����ȡ���Ի����顣';
  }
  
  // ����Ƿ�ʹ��Mockģʽ
  static isMockMode(): boolean {
    // ����ͨ�����û򻷾������������Ƿ�����Mockģʽ
    return true;
  }
}