/**
 * PWA 모바일 상태바 색상을 동적으로 제어하기 위한 유틸리티
 * @param {string} color - 설정할 색상 (예: '#5E58FB')
 */
export const setThemeColor = (color) => {
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content', color);
  }
};
