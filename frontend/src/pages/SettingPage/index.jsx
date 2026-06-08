import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { PageButton } from 'src/components/Button'
import Layout from 'src/components/Layout'
import { SettingTopContainer } from 'src/components/TopContainer'
import { GLOBAL_CONFIG } from 'src/settings'
import { setThemeColor } from 'src/utils/theme'
import styles from './SettingPage.module.css'

function SettingPage() {
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const [isExiting, setIsExiting] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState(() => {
    return localStorage.getItem('app_language') || 'ko'
  })

  const handleTransition = (path) => {
    setIsExiting(true)
    setTimeout(() => navigate(path), 500)
  }

  useEffect(() => {
    document.body.style.backgroundColor = 'var(--color-bg)'
    setThemeColor(GLOBAL_CONFIG.colorBg)

    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  const handleSave = () => {
    localStorage.setItem('app_language', selectedLanguage)
    i18n.changeLanguage(selectedLanguage)
    handleTransition('/home')
  }

  return (
    <Layout className={`${styles.layout} ${isExiting ? styles.fadeOut : ''}`}>
      <div className={styles.mainContainer}>
        {/* SettingTopContainer */}
        <SettingTopContainer onBack={() => handleTransition('/home')} />

        {/* Setting Title */}
        <h1 className={styles.title}>{t('setting_title')}</h1>

        {/* Setting Items */}
        <div className={styles.settingList}>
          <div className={styles.settingItem}>
            <div className={styles.settingItemLabel}>{t('setting_lang_label')}</div>
            <div className={styles.languageOptions}>
              <button
                type="button"
                className={`${styles.langButton} ${selectedLanguage === 'ko' ? styles.active : ''}`}
                onClick={() => setSelectedLanguage('ko')}
              >
                한국어
              </button>
              <button
                type="button"
                className={`${styles.langButton} ${selectedLanguage === 'en' ? styles.active : ''}`}
                onClick={() => setSelectedLanguage('en')}
              >
                English
              </button>
              <button
                type="button"
                className={`${styles.langButton} ${selectedLanguage === 'ru' ? styles.active : ''}`}
                onClick={() => setSelectedLanguage('ru')}
              >
                Русский
              </button>
            </div>
          </div>
        </div>

      </div>

      {/* Bottom Save Button Area */}
      <div className={styles.bottomArea}>
        <div className={styles.buttonWrapper}>
          <PageButton
            label={t('setting_save')}
            onClick={handleSave}
          />
        </div>
      </div>
    </Layout>
  )
}

export default SettingPage
