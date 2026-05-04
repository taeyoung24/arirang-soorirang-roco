/**
 * 백엔드 서버와의 통신을 위한 기본 API 클라이언트 설정
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

/**
 * 기본 fetch 래퍼 함수 (향후 axios로 교체 가능)
 * @param {string} endpoint - API 엔드포인트
 * @param {object} options - fetch 옵션 (method, headers, body 등)
 */
export const apiClient = async (endpoint, options = {}) => {
  const url = `${BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    
    // 응답 에러 처리
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || 'API 요청에 실패했습니다.');
    }

    // 데이터가 없는 경우 처리
    if (response.status === 204) return null;

    return await response.json();
  } catch (error) {
    console.error('API 통신 오류:', error);
    throw error;
  }
};

export default apiClient;
