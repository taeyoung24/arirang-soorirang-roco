import { GLOBAL_CONFIG } from 'src/settings'

const API_PREFIX = '/api/v1'
const API_BASE_URL = GLOBAL_CONFIG.API_BASE_URL.replace(/\/$/, '')

const frontendAssets = import.meta.glob('/src/assets/**/*.{png,jpg,jpeg,webp,svg}', {
  eager: true,
  import: 'default',
  query: '?url',
})

const FRONTEND_ASSET_BY_NAME = Object.fromEntries(
  Object.entries(frontendAssets).map(([path, url]) => [
    path.split('/').pop(),
    url,
  ])
)

const FRONTEND_ASSET_ALIASES = {
  'bank.png': 'word-image-snow.png',
  'bird-write.png': 'word-image-write.png',
  'hospital.png': 'word-image-write.png',
  'placeholder.png': 'word-image-snow.png',
  'school.png': 'word-image-write.png',
  'tiger-cap.png': 'word-image-snow.png',
  'tiger-snow.png': 'word-image-snow.png',
}

const resolveFrontendAsset = (url) => {
  const assetName = url.split('/').pop()
  const aliasName = FRONTEND_ASSET_ALIASES[assetName] || assetName

  return FRONTEND_ASSET_BY_NAME[aliasName]
}

export const resolveAssetUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('/sentence_images/')) return url
  const frontendAsset = resolveFrontendAsset(url)
  if (frontendAsset) return frontendAsset
  if (/^https?:\/\//.test(url)) return url
  return `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`
}

export const resolveMediaUrl = (url) => {
  if (!url) return ''
  if (/^https?:\/\//.test(url)) return url
  return url.startsWith('/') ? url : `/${url}`
}

/**
 * 기본 fetch 래퍼 함수 (향후 axios로 교체 가능)
 * @param {string} endpoint - API 엔드포인트
 * @param {object} options - fetch 옵션 (method, headers, body 등)
 */
export const apiClient = async (endpoint, options = {}) => {
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  const url = `${API_BASE_URL}${API_PREFIX}${path}`
  const isFormData = options.body instanceof FormData
  
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers,
  }

  const config = {
    ...options,
    headers,
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || 'API 요청에 실패했습니다.')
    }

    if (response.status === 204) return null

    const payload = await response.json()

    if (payload && payload.success === false) {
      throw new Error(payload.message || 'API 요청에 실패했습니다.')
    }

    return payload && Object.prototype.hasOwnProperty.call(payload, 'data')
      ? payload.data
      : payload
  } catch (error) {
    console.error('API 통신 오류:', error)
    throw error
  }
}

export const getRecommendedContents = () => apiClient('/contents/recommended')

export const getRecentContents = () => apiClient('/contents/recent')

export const getCategories = () => apiClient('/categories')

export const getCategorySets = (categoryId) => (
  apiClient(`/categories/${categoryId}/sets`)
)

export const getSetCards = (setId) => apiClient(`/sets/${setId}/cards`)

export const submitCardAnswer = (cardId, choiceId) => (
  apiClient(`/cards/${cardId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ choice_id: choiceId }),
  })
)

export const evaluatePronunciation = (cardId, formData) => (
  apiClient(`/cards/${cardId}/pronunciation`, {
    method: 'POST',
    body: formData,
  })
)

export const getSavedWords = () => apiClient('/saved-words')

export default apiClient
