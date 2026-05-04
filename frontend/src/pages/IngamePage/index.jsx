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
  
  // 무한 스와이프를 위한 스테이지 상태
  const [stageCount, setStageCount] = useState(1)
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    // 배경색을 피그마 디자인에 맞춰 yellow-primary로 변경
    document.body.style.backgroundColor = 'var(--color-yellow-primary)'
    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  // 스테이지 클리어 시 다음 스테이지 미리 렌더링 허용
  const handleStageUnlock = () => {
    setIsStageUnlocked(true)
    if (stageCount === currentIndex + 1) {
      setStageCount(prev => prev + 1)
    }
  }

  // 스크롤 이벤트로 화면 전환 감지
  const handleScroll = (e) => {
    const { scrollTop, clientHeight } = e.target
    // 현재 가장 많이 보여지는 화면의 인덱스 계산
    const newIndex = Math.round(scrollTop / clientHeight)
    
    // 다음 화면으로 완전히 넘어갔을 때
    if (newIndex > currentIndex) {
      setCurrentIndex(newIndex)
      setIsStageUnlocked(false) // 다시 스테이지 잠금 상태로
    } else if (newIndex < currentIndex) {
      // 이전 스테이지로 돌아갔을 때
      setCurrentIndex(newIndex)
      setIsStageUnlocked(true) // 이전 스테이지는 이미 클리어했으므로 잠금 해제 유지
    }
  }

  return (
    <Layout className="bg-yellow-primary h-screen flex flex-col justify-start">
      <div className="w-80 h-[718px] max-h-full mx-auto flex flex-col justify-start items-center gap-4">

        {/* Header */}
        <IngameTopContainer 
          onBack={() => navigate('/home')} 
          onHelp={() => { }} 
          status={isStageUnlocked ? 'unlocked' : 'locked'} 
        />

        {/* View Routing / Scrollable Swipe Area */}
        <div 
          onScroll={handleScroll}
          className={`self-stretch flex-1 flex flex-col snap-y snap-mandatory ${
            isStageUnlocked ? 'overflow-y-scroll' : 'overflow-y-hidden'
          } [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]`}
        >
          {Array.from({ length: stageCount }).map((_, index) => (
            <div key={index} className="snap-start snap-always w-full h-full flex-shrink-0 flex flex-col pb-4">
              {currentStep === 'quiz' && <QuizView onStageUnlock={handleStageUnlock} />}
            </div>
          ))}
        </div>

      </div>
    </Layout>
  )
}
