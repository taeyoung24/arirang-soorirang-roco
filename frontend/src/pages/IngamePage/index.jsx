import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getSetCards } from 'src/api'
import Layout from 'src/components/Layout'
import { IngameTopContainer } from 'src/components/TopContainer'
import QuizView from './views/QuizView'

export default function IngamePage() {
  const navigate = useNavigate()
  const { setId } = useParams()

  // 게임 흐름을 제어하는 상태 ('quiz' | 'stats' | 'pronounce' | 'result')
  const [currentStep] = useState('quiz')
  const [isStageUnlocked, setIsStageUnlocked] = useState(false)
  const [setData, setSetData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const missingSetMessage = setId ? '' : '학습 세트를 먼저 선택하세요.'

  useEffect(() => {
    // 배경색을 피그마 디자인에 맞춰 yellow-primary로 변경
    document.body.style.backgroundColor = 'var(--color-yellow-primary)'
    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  useEffect(() => {
    if (!setId) {
      return
    }

    let isMounted = true

    async function loadSetCards() {
      try {
        setIsLoading(true)
        const data = await getSetCards(setId)

        if (!isMounted) return

        setSetData(data)
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
  }, [setId])

  return (
    <Layout className="bg-yellow-primary min-h-screen pb-8">
      <div className="w-80 min-h-[718px] mx-auto flex flex-col justify-start items-center gap-4">

        {/* Header */}
        <IngameTopContainer 
          onBack={() => navigate('/home')} 
          onHelp={() => { }} 
          status={isStageUnlocked ? 'unlocked' : 'locked'} 
        />

        {/* View Routing */}
        {isLoading && (
          <div className="self-stretch flex-1 flex justify-center items-center text-text text-lg font-extrabold font-sans">
            불러오는 중
          </div>
        )}

        {!isLoading && (missingSetMessage || errorMessage) && (
          <div className="self-stretch flex-1 flex flex-col justify-center items-center gap-4 text-center">
            <p className="text-text text-lg font-extrabold font-sans">
              {missingSetMessage || errorMessage}
            </p>
            <button
              onClick={() => navigate('/selection')}
              className="h-11 px-5 bg-bg rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text text-text text-base font-extrabold font-sans"
            >
              세트 고르기
            </button>
          </div>
        )}

        {!isLoading && !missingSetMessage && !errorMessage && currentStep === 'quiz' && (
          <QuizView
            cards={setData?.cards || []}
            title={setData?.title || ''}
            onStageUnlock={() => setIsStageUnlocked(true)}
          />
        )}

        {/* 추후 구현될 화면들: */}
        {/* {currentStep === 'stats' && <StatsOverlay />} */}
        {/* {currentStep === 'pronounce' && <PronounceView />} */}
        {/* {currentStep === 'result' && <ResultView />} */}

      </div>
    </Layout>
  )
}
