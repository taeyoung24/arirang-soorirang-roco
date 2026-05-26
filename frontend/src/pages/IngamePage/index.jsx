import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from 'src/components/Layout'
import { IngameTopContainer } from 'src/components/TopContainer'
import { GLOBAL_CONFIG } from 'src/settings'
import { setThemeColor } from 'src/utils/theme'
import styles from './IngamePage.module.css'
import QuizView from './views/QuizView'

export default function IngamePage() {
  const navigate = useNavigate()

  // 게임 흐름을 제어하는 상태 ('quiz' | 'stats' | 'pronounce' | 'result')
  const [currentStep, setCurrentStep] = useState('quiz')
  const [isStageUnlocked, setIsStageUnlocked] = useState(false)
  const [isExiting, setIsExiting] = useState(false)
  const [isBouncing, setIsBouncing] = useState(false)

  // 무한 스와이프를 위한 스테이지 상태
  const [stageCount, setStageCount] = useState(1)
  const [currentIndex, setCurrentIndex] = useState(0)

  // 스크롤 핸들러 최적화용 ref
  const currentIndexRef = useRef(0)  // 클로저 stale 문제 방지용 최신 인덱스 ref
  const rafRef = useRef(null)         // requestAnimationFrame throttle용 ref

  useEffect(() => {
    // 배경색을 피그마 디자인에 맞춰 yellow-primary로 변경
    document.body.style.backgroundColor = 'var(--color-yellow-primary)'
    setThemeColor(GLOBAL_CONFIG.colorYellowPrimary)

    return () => {
      document.body.style.backgroundColor = ''
      setThemeColor(GLOBAL_CONFIG.colorBg)
    }
  }, [])

  const handleBack = () => {
    setIsExiting(true)
    document.body.style.backgroundColor = 'var(--color-bg)'
    setTimeout(() => navigate('/home'), 500)
  }

  // 스테이지 클리어 시 다음 스테이지 미리 렌더링 허용
  const handleStageUnlock = () => {
    setIsStageUnlocked(true)
    if (stageCount === currentIndex + 1) {
      setStageCount(prev => prev + 1)
    }

    // 결과창(step 4) 페이드인이 완료된 시점(약 400ms 후)에 찰지게 튕기는 힌트 모션 동작!
    setTimeout(() => {
      setIsBouncing(true)
      // 애니메이션 시간(1400ms) 완료 후 상태 초기화
      setTimeout(() => {
        setIsBouncing(false)
      }, 1400)
    }, 400)
  }

  // 스크롤 이벤트로 화면 전환 감지 (requestAnimationFrame 쓰로틀링 적용)
  const handleScroll = useCallback((e) => {
    // 이미 RAF가 예약된 경우 중복 호출 무시 → 프레임당 최대 1회만 실행
    if (rafRef.current) return

    const target = e.target  // 이벤트 객체는 RAF 콜백 전에 풀링될 수 있으므로 미리 캡처
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null
      const { scrollTop, clientHeight } = target
      const newIndex = Math.round(scrollTop / clientHeight)

      // ref로 최신 인덱스 비교 (stale closure 방지)
      if (newIndex > currentIndexRef.current) {
        currentIndexRef.current = newIndex
        setCurrentIndex(newIndex)
        setIsStageUnlocked(false)
      } else if (newIndex < currentIndexRef.current) {
        currentIndexRef.current = newIndex
        setCurrentIndex(newIndex)
        setIsStageUnlocked(true)
      }
    })
  }, [])

  return (
    <Layout className={`${styles.layout} ${styles.fadeIn} ${isExiting ? styles.fadeOut : ''}`}>
      {isBouncing && <div className={styles.topAmbientGlow} />}
      <div className={styles.mainContainer}>

        {/* Header */}
        <IngameTopContainer
          onBack={handleBack}
          onHelp={() => { }}
          status={isStageUnlocked ? 'unlocked' : 'locked'}
        />

        {/* View Routing / Scrollable Swipe Area */}
        <div
          onScroll={handleScroll}
          className={`${styles.scrollArea} ${
            isStageUnlocked ? styles.scrollUnlocked : styles.scrollLocked
          }`}
        >
          {/* bounceHint 애니메이션을 스크롤 컨테이너와 분리하여 GPU 컴포지터 충돌 방지 */}
          <div className={`${styles.bounceWrapper} ${isBouncing ? styles.bounceHint : ''}`}>
            {Array.from({ length: stageCount }).map((_, index) => (
              <div key={index} className={styles.stageItem}>
                {currentStep === 'quiz' && <QuizView onStageUnlock={handleStageUnlock} />}
              </div>
            ))}
          </div>
        </div>

      </div>
    </Layout>
  )
}
