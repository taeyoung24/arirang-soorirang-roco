import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import header from 'src/assets/landing-header.svg'
import mascot from 'src/assets/landing-mascot.svg'
import { PageButton } from 'src/components/Button'
import Layout from 'src/components/Layout'

function LandingPage() {
  const navigate = useNavigate()

  useEffect(() => {
    document.body.style.backgroundColor = '#5E58FB'
    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  return (
    <Layout>
      <div className="bg-landing-page-primary h-screen overflow-hidden relative -mx-[36px] -my-[52px]">

        {/* Header (top) */}
        <div className="absolute top-24 left-1/2 -translate-x-1/2">
          <img src={header} alt="아리랑 수리랑" className="max-w-max" />
        </div>

        {/* Mascot (middle-ish, slightly above center) */}
        <div className=" absolute top-[50%] left-1/2 -translate-x-1/2 -translate-y-1/2">
          <img src={mascot} alt="mascot" className="max-w-dvw" />
        </div>

        {/* Bottom section */}
        <div className="absolute bottom-10 left-0 w-full flex flex-col items-center gap-14 px-6">
          <p className="w-10/12 text-white text-s text-center opacity-70">
            시작하기 버튼을 누르면 이용약관 및 개인정보 처리방침에 동의하는 것으로 간주합니다.
          </p>

          <PageButton
            onClick={() => navigate('/home')}
            className="w-10/12"
          >
            로그인 없이 시작
          </PageButton>
        </div>
      </div>
    </Layout>
  )
}

export default LandingPage;
