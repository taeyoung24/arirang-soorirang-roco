import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import header from 'src/assets/landing-header.svg'
import mascot from 'src/assets/landing-mascot.svg'
import { PageButton } from 'src/components/Button'
import Layout from 'src/components/Layout'

function LandingPage() {
  const navigate = useNavigate()

  useEffect(() => {
    document.body.style.backgroundColor = 'var(--color-soori-primary)'
    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  return (
    <Layout className="bg-soori-primary h-[770px]">
      {/* Main Content Area (Header, Mascot, Terms) */}
      <div className="w-80 h-[718px] mx-auto flex flex-col justify-between items-center">

        {/* Header section */}
        <div className="self-stretch h-48 py-12 flex flex-col justify-center items-center">
          <img src={header} alt="아리랑 수리랑" className="w-[289px] h-auto" />
        </div>

        {/* Mascot section with Shadows */}
        <div className="relative flex flex-col items-center justify-center">
          <div className="absolute bottom-4 flex gap-4">
            <div className="w-28 h-3 bg-black/20 rounded-full" />
            <div className="w-28 h-3 bg-black/20 rounded-full" />
          </div>
          <img src={mascot} alt="mascot" className="w-80 h-auto relative z-10" />
        </div>

        {/* Bottom container (Terms Only) */}
        <div className="self-stretch h-36 flex justify-center items-center">
          <div className="text-center px-4">
            <span className="text-white-primary text-xs font-normal font-sans">시작하기 버튼을 누르면 </span>
            <span className="text-white-primary text-xs font-normal font-sans underline cursor-pointer">이용약관</span>
            <span className="text-white-primary text-xs font-normal font-sans"> 및 </span>
            <span className="text-white-primary text-xs font-normal font-sans underline cursor-pointer">개인정보 처리방침</span>
            <span className="text-white-primary text-xs font-normal font-sans">에 동의하는 것으로 간주합니다.</span>
          </div>
        </div>
      </div>

      {/* Absolute Positioned Button */}
      <div className="absolute bottom-10 left-1/2 -translate-x-1/2">
        <PageButton
          onClick={() => navigate('/home')}
          className="w-80"
        >
          로그인 없이 시작
        </PageButton>
      </div>
    </Layout>
  )
}


export default LandingPage;
