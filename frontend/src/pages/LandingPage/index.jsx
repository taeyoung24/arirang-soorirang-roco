import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import ariImg from 'src/assets/landing-frame-ari.png'
import shadowImg from 'src/assets/landing-frame-shadow.png'
import sooriImg from 'src/assets/landing-frame-soori.png'
import header from 'src/assets/landing-header.svg'
import { PageButton } from 'src/components/Button'
import Layout from 'src/components/Layout'
import { GLOBAL_CONFIG } from 'src/settings'
import { setThemeColor } from 'src/utils/theme'
import styles from './LandingPage.module.css'

function LandingPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    document.body.style.backgroundColor = 'var(--color-soori-primary)'
    setThemeColor(GLOBAL_CONFIG.colorSooriPrimary)

    return () => {
      document.body.style.backgroundColor = ''
      setThemeColor(GLOBAL_CONFIG.colorBg)
    }
  }, [])

  return (
    <Layout className={`${styles.layout} ${isExiting ? styles.fadeOut : ''}`}>
      {/* Main Content Area (Header, Mascot) */}
      <div className={styles.mainContent}>

        {/* Header section */}
        <div className={styles.header}>
          <img src={header} alt="아리랑 수리랑" className={styles.headerImg} />
        </div>

        {/* Mascot section */}
        <div className={styles.mascotSection}>
          <img src={shadowImg} alt="shadow" className={styles.mascotShadow} />
          <img src={ariImg} alt="ari" className={styles.mascotAri} />
          <img src={sooriImg} alt="soori" className={styles.mascotSoori} />
        </div>
      </div>

      {/* Bottom Container (Terms + Button) */}
      <div className={styles.bottomArea}>
        <div className={styles.termsContainer}>
          <div className={styles.termsTextWrapper}>
            <span className={styles.termsText}>{t('terms_prefix')}</span>
            <span className={styles.termsLink}>{t('terms_link_service')}</span>
            <span className={styles.termsText}>{t('terms_and')}</span>
            <span className={styles.termsLink}>{t('terms_link_privacy')}</span>
            <span className={styles.termsText}>{t('terms_suffix')}</span>
          </div>
        </div>

        <div className={styles.buttonWrapper}>
          <PageButton
            label={t('btn_start_without_login')}
            onClick={() => {
              setIsExiting(true)
              document.body.style.backgroundColor = 'var(--color-bg)'
              setTimeout(() => navigate('/home'), 500)
            }}
          />
        </div>
      </div>
    </Layout>
  )
}


export default LandingPage;
