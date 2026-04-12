import { useNavigate } from 'react-router-dom'
import mascot from '../../assets/landing-mascot.svg'
import header from '../../assets/landing-header.svg'

function LandingPage() {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col min-h-screen bg-primary px-6 pt-12 pb-10">
      <img src={header} alt="아리랑 수리랑" className="w-64 mx-auto" />

      <div className="flex-1 flex items-center justify-center">
        <img src={mascot} alt="mascot" className="w-72" />
      </div>

      <div className="w-full flex flex-col items-center gap-4">
        <p className="text-white text-xs text-center opacity-70">
          시작하기 버튼을 누르면 이용약관 및 개인정보 처리방침에 동의하는 것으로 간주합니다.
        </p>
        <button
          onClick={() => navigate('/home')}
          className="w-full bg-bg-light rounded-full py-4 text-lg font-semibold text-text-main"
        >
          로그인 없이 시작
        </button>
      </div>
    </div>
  )
}

export default LandingPage
