import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from 'src/components/Layout'
import { IngameTopContainer } from 'src/components/TopContainer'
import QuizView from './views/QuizView'

export default function IngamePage() {
  const navigate = useNavigate()

  // 게임 흐름을 제어하는 상태 ('quiz' | 'stats' | 'pronounce' | 'result')
  const [currentStep, setCurrentStep] = useState('quiz')
  const [isStageUnlocked, setIsStageUnlocked] = useState(false)

  useEffect(() => {
    // 배경색을 피그마 디자인에 맞춰 yellow-primary로 변경
    document.body.style.backgroundColor = 'var(--color-yellow-primary)'
    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  return (
    <Layout className="bg-yellow-primary h-[770px]">
      <div className="w-80 h-[718px] mx-auto flex flex-col justify-start items-center gap-4">

        {/* Header */}
        <IngameTopContainer 
          onBack={() => navigate('/home')} 
          onHelp={() => { }} 
          status={isStageUnlocked ? 'unlocked' : 'locked'} 
        />

        {/* View Routing */}
        {currentStep === 'quiz' && <QuizView onStageUnlock={() => setIsStageUnlocked(true)} />}

        {/* 추후 구현될 화면들: */}
        {/* {currentStep === 'stats' && <StatsOverlay />} */}
        {/* {currentStep === 'pronounce' && <PronounceView />} */}
        {/* {currentStep === 'result' && <ResultView />} */}

      </div>
    </Layout>
  )
}
