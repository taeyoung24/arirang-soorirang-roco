import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { getSetCards } from 'src/api'
import Layout from 'src/components/Layout'
import { IngameTopContainer } from 'src/components/TopContainer'
import { GLOBAL_CONFIG } from 'src/settings'
import { setThemeColor } from 'src/utils/theme'
import styles from './IngamePage.module.css'
import QuizView from './views/QuizView'

export default function IngamePage() {
  const navigate = useNavigate()
  const { setId } = useParams()
  const [searchParams] = useSearchParams()
  const selectedWord = searchParams.get('word') || ''
  const selectedCardId = searchParams.get('card') || ''

  const [currentStep] = useState('quiz')
  const [isStageUnlocked, setIsStageUnlocked] = useState(false)
  const [isExiting, setIsExiting] = useState(false)
  const [isBouncing, setIsBouncing] = useState(false)
  const [stageCount, setStageCount] = useState(1)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [setData, setSetData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const currentIndexRef = useRef(0)
  const rafRef = useRef(null)
  const missingSetMessage = setId ? '' : '학습 세트를 먼저 선택하세요.'

  useEffect(() => {
    document.body.style.backgroundColor = 'var(--color-yellow-primary)'
    setThemeColor(GLOBAL_CONFIG.colorYellowPrimary)

    return () => {
      document.body.style.backgroundColor = ''
      setThemeColor(GLOBAL_CONFIG.colorBg)
    }
  }, [])

  useEffect(() => {
    if (!setId) return

    let isMounted = true

    async function loadSetCards() {
      try {
        setIsLoading(true)
        const data = await getSetCards(setId)
        const filteredCards = selectedCardId
          ? data.cards.filter((card) => card.card_id === selectedCardId)
          : selectedWord
          ? data.cards.filter((card) => card.polysemy_word === selectedWord)
          : data.cards

        if (!isMounted) return

        setSetData({
          ...data,
          title: selectedWord ? `${data.title} · ${selectedWord}` : data.title,
          cards: filteredCards,
        })
        setStageCount(1)
        setCurrentIndex(0)
        currentIndexRef.current = 0
        setIsStageUnlocked(false)
        setErrorMessage('')
      } catch (error) {
        if (!isMounted) return

        console.error('학습 카드를 불러오지 못했습니다:', error)
        setErrorMessage(error.message)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadSetCards()

    return () => {
      isMounted = false
    }
  }, [setId, selectedWord, selectedCardId])

  const handleBack = () => {
    setIsExiting(true)
    document.body.style.backgroundColor = 'var(--color-bg)'
    setTimeout(() => navigate('/home'), 500)
  }

  const handleStageUnlock = () => {
    setIsStageUnlocked(true)
    const cardCount = setData?.cards?.length || 0

    if (stageCount === currentIndex + 1 && stageCount < cardCount) {
      setStageCount((prev) => prev + 1)
    }

    setTimeout(() => {
      setIsBouncing(true)
      setTimeout(() => {
        setIsBouncing(false)
      }, 1400)
    }, 400)
  }

  const handleScroll = useCallback((e) => {
    if (rafRef.current) return

    const target = e.target
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = null
      const { scrollTop, clientHeight } = target
      const newIndex = Math.round(scrollTop / clientHeight)

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

  const renderMessage = (message) => (
    <div className={styles.scrollArea}>
      <div className={styles.stageItem}>
        <p>{message}</p>
        <button onClick={() => navigate('/selection')}>세트 고르기</button>
      </div>
    </div>
  )

  const cards = setData?.cards || []

  return (
    <Layout className={`${styles.layout} ${styles.fadeIn} ${isExiting ? styles.fadeOut : ''}`}>
      {isBouncing && <div className={styles.topAmbientGlow} />}
      <div className={styles.mainContainer}>
        <IngameTopContainer
          onBack={handleBack}
          onHelp={() => { }}
          status={isStageUnlocked ? 'unlocked' : 'locked'}
        />

        {isLoading && renderMessage('불러오는 중')}
        {!isLoading && (missingSetMessage || errorMessage) && renderMessage(missingSetMessage || errorMessage)}
        {!isLoading && !missingSetMessage && !errorMessage && cards.length === 0 && renderMessage('학습 카드가 없습니다.')}

        {!isLoading && !missingSetMessage && !errorMessage && cards.length > 0 && (
          <div
            onScroll={handleScroll}
            className={`${styles.scrollArea} ${
              isStageUnlocked ? styles.scrollUnlocked : styles.scrollLocked
            }`}
          >
            <div className={`${styles.bounceWrapper} ${isBouncing ? styles.bounceHint : ''}`}>
              {Array.from({ length: stageCount }).map((_, index) => (
                <div key={index} className={styles.stageItem}>
                  {currentStep === 'quiz' && (
                    <QuizView
                      key={cards[index]?.card_id}
                      card={cards[index]}
                      title={setData?.title || ''}
                      progress={`${index + 1}/${cards.length}`}
                      onStageUnlock={handleStageUnlock}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
