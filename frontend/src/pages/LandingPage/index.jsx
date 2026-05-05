import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import header from 'src/assets/landing-header.svg'
import mascot from 'src/assets/landing-mascot.svg'
import { PageButton } from 'src/components/Button'
import Layout from 'src/components/Layout'
import styles from './LandingPage.module.css'

function LandingPage() {
  const navigate = useNavigate()

  useEffect(() => {
    document.body.style.backgroundColor = 'var(--color-soori-primary)'
    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  return (
    <Layout className={styles.layout}>
      {/* Main Content Area (Header, Mascot, Terms) */}
      <div className={styles.mainContent}>

        {/* Header section */}
        <div className={styles.header}>
          <img src={header} alt="아리랑 수리랑" className={styles.headerImg} />
        </div>

        {/* Mascot section with Shadows */}
        <div className={styles.mascotSection}>
          <img src={mascot} alt="mascot" className={styles.mascotImg} />
        </div>

        {/* Bottom container (Terms Only) */}
        <div className={styles.termsContainer}>
          <div className={styles.termsTextWrapper}>
            <span className={styles.termsText}>시작하기 버튼을 누르면 </span>
            <span className={styles.termsLink}>이용약관</span>
            <span className={styles.termsText}> 및 </span>
            <span className={styles.termsLink}>개인정보 처리방침</span>
            <span className={styles.termsText}>에 동의하는 것으로 간주합니다.</span>
          </div>
        </div>
      </div>

      {/* Absolute Positioned Button */}
      <div className={styles.buttonWrapper}>
        <PageButton
          label="로그인 없이 시작"
          onClick={() => navigate('/home')}
        />
      </div>
    </Layout>
  )
}


export default LandingPage;
