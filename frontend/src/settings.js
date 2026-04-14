/**
 * 필수 환경 변수를 가져오거나 기본값을 반환합니다.
 * Vite 환경에서는 import.meta.env를 통해 VITE_ 접두사가 붙은 변수에 접근합니다.
 */
function requireEnv(key, defaultValue) {
  const value = import.meta.env[key];

  if (value === undefined) {
    if (defaultValue !== undefined) {
      if (import.meta.env.DEV) {
        console.warn(`[Config] '${key}' is not defined. Using default: '${defaultValue}'`);
      }
      return defaultValue;
    }
    throw new Error(`[Config] Critical error: Environment variable '${key}' is missing.`);
  }

  return value;
}

export const GLOBAL_CONFIG = {
  API_BASE_URL: requireEnv('VITE_API_BASE_URL', 'http://localhost:3000'),
  MODE: import.meta.env.MODE,
  IS_DEV: import.meta.env.DEV,
};

