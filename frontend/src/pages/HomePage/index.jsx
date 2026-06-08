import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  resolveAssetUrl,
} from 'src/api'
import mascot from 'src/assets/landing-mascot.svg'
import normalMascot from 'src/assets/mascot/word-image-snow.png'
import winterMascot from 'src/assets/mascot/word-image-write.png'
import BottomNav from 'src/components/BottomNav'
import Layout from 'src/components/Layout'
import { HomeTopContainer } from 'src/components/TopContainer'
import { GLOBAL_CONFIG } from 'src/settings'
import { setThemeColor } from 'src/utils/theme'
import styles from './HomePage.module.css'


function ContentCard({ title, image, onClick }) {
  return (
    <div className={styles.contentCard} onClick={onClick} style={{ cursor: 'pointer' }}>
      <div className={styles.contentCardTitle}>
        {title}
      </div>
      <div className={styles.contentCardDivider} />
      <img src={image} alt={title} className={styles.contentCardImg} />
    </div>
  )
}



function ContentSection({ label, bg, cards }) {
  return (
    <div className={styles.contentSectionWrap}>
      <div className={`${styles.contentSectionBlob} ${bg === 'bg-soori-primary' ? styles.bgSooriPrimary : styles.bgSoftDark}`}>
        <div className={styles.contentList}>
          {cards.map((card, i) => (
            <ContentCard
              key={card.id || i}
              title={card.title}
              image={card.image}
              onClick={card.onClick}
            />
          ))}
        </div>
      </div>
      <div className={styles.contentSectionLabel}>
        <div className={styles.contentSectionLabelText}>{label}</div>
      </div>
    </div>
  )
}




function HomePage() {
  const navigate = useNavigate()
  const { t, i18n } = useTranslation()
  const [isExiting, setIsExiting] = useState(false)
  const [recommendedCards, setRecommendedCards] = useState([])
  const [recentCards, setRecentCards] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  const handleTransition = useCallback((path, bgColor) => {
    setIsExiting(true)
    if (bgColor) {
      document.body.style.backgroundColor = bgColor
    }
    setTimeout(() => navigate(path), 500)
  }, [navigate])

  useEffect(() => {
    document.body.style.backgroundColor = 'var(--color-bg)'
    setThemeColor(GLOBAL_CONFIG.colorBg)

    return () => {
      document.body.style.backgroundColor = ''
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    function loadHomeContents() {
      try {
        if (!isMounted) return

        setRecommendedCards(
          [
            {
              id: 'demo_recommended_school',
              title: t('demo_set_high_school'),
              image: winterMascot,
              onClick: () => handleTransition('/ingame/set_school_01', 'var(--color-yellow-primary)'),
            },
            {
              id: 'demo_recommended_basic',
              title: t('demo_set_daily_conversation'),
              image: normalMascot,
              onClick: () => handleTransition('/ingame/set_test_01', 'var(--color-yellow-primary)'),
            },
            {
              id: 'demo_recommended_cafe',
              title: t('demo_set_cafe'),
              image: resolveAssetUrl('/sentence_images/84f541d7.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?word=%EC%B0%A8',
                'var(--color-yellow-primary)'
              ),
            },
            {
              id: 'demo_recommended_friends',
              title: t('demo_set_hanging_out'),
              image: resolveAssetUrl('/sentence_images/0098f302.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?word=%EB%A7%9E%EB%8B%A4',
                'var(--color-yellow-primary)'
              ),
            },
            {
              id: 'demo_recommended_move',
              title: t('demo_set_transportation'),
              image: resolveAssetUrl('/sentence_images/a303d7dd.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?word=%ED%83%80%EB%8B%A4',
                'var(--color-yellow-primary)'
              ),
            },
          ]
        )
        setRecentCards(
          [
            {
              id: 'demo_recent_mal',
              title: t('demo_word_mal'),
              image: resolveAssetUrl('/sentence_images/db02d205.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?card=card_db02d205',
                'var(--color-yellow-primary)'
              ),
            },
            {
              id: 'demo_recent_tada_ride',
              title: t('demo_word_tada'),
              image: resolveAssetUrl('/sentence_images/a303d7dd.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?card=card_a303d7dd',
                'var(--color-yellow-primary)'
              ),
            },
            {
              id: 'demo_recent_tada_award',
              title: t('demo_word_tada'),
              image: resolveAssetUrl('/sentence_images/0d335015.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?card=card_0d335015',
                'var(--color-yellow-primary)'
              ),
            },
            {
              id: 'demo_recent_matda',
              title: t('demo_word_matda'),
              image: resolveAssetUrl('/sentence_images/0098f302.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?card=card_0098f302',
                'var(--color-yellow-primary)'
              ),
            },
            {
              id: 'demo_recent_cha',
              title: t('demo_word_cha'),
              image: resolveAssetUrl('/sentence_images/84f541d7.png'),
              onClick: () => handleTransition(
                '/ingame/set_test_01?card=card_84f541d7',
                'var(--color-yellow-primary)'
              ),
            },
          ]
        )
      } catch (error) {
        if (!isMounted) return

        console.error('홈 콘텐츠를 불러오지 못했습니다:', error)
        setRecommendedCards([
          { id: 'fallback_school', title: t('demo_set_high_school'), image: winterMascot },
          { id: 'fallback_basic', title: t('demo_set_daily_conversation'), image: normalMascot },
          { id: 'fallback_cafe', title: t('demo_set_cafe'), image: normalMascot },
        ])
        setRecentCards([
          { id: 'fallback_recent_1', title: t('demo_word_sseuda'), image: normalMascot },
          { id: 'fallback_recent_2', title: t('demo_word_bae'), image: winterMascot },
        ])
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadHomeContents()

    return () => {
      isMounted = false
    }
  }, [handleTransition, i18n.language, t])

  return (
    <Layout className={`${styles.layout} ${isExiting ? styles.fadeOut : ''}`}>
      <div className={styles.mainContainer}>

        {/* HomeTopContainer */}
        <HomeTopContainer mascotSrc={mascot} onMenu={() => handleTransition('/setting', 'var(--color-bg)')} />



        {/* Title */}
        <h1 className={styles.title}>
          {t('home_title')}
        </h1>

        {/* Login Banner */}
        {/* <div className={styles.loginBanner}>
          <p className={styles.loginTitle}>로그인</p>
          <p className={styles.loginDesc}>더 나은 학습을 위해 로그인하세요.</p>
          <div className={styles.loginIconWrapper}>
            <svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
              <mask id="path-1-inside-1_254_560" fill="white">
                <path d="M0 26C0 11.6406 11.6406 0 26 0C40.3594 0 52 11.6406 52 26C52 40.3594 40.3594 52 26 52C11.6406 52 0 40.3594 0 26Z" />
              </mask>
              <path d="M0 26C0 11.6406 11.6406 0 26 0C40.3594 0 52 11.6406 52 26C52 40.3594 40.3594 52 26 52C11.6406 52 0 40.3594 0 26Z" fill="var(--text-dimmed, #7D7D7D)" />
              <path d="M0 26M52 26M52 26M0 26M26 0M52 26M26 52M0 26M26 52V49.6C12.9661 49.6 2.4 39.0339 2.4 26H0H-2.4C-2.4 41.6849 10.3151 54.4 26 54.4V52ZM52 26H49.6C49.6 39.0339 39.0339 49.6 26 49.6V52V54.4C41.6849 54.4 54.4 41.6849 54.4 26H52ZM26 0V2.4C39.0339 2.4 49.6 12.9661 49.6 26H52H54.4C54.4 10.3151 41.6849 -2.4 26 -2.4V0ZM26 0V-2.4C10.3151 -2.4 -2.4 10.3151 -2.4 26H0H2.4C2.4 12.9661 12.9661 2.4 26 2.4V0Z" fill="var(--text, #2C2C2C)" mask="url(#path-1-inside-1_254_560)" />
            </svg>
          </div>
        </div> */}

        {/* Search */}
        <div
          onClick={() => handleTransition('/selection')}
          className={styles.searchBox}
        >

          <p className={styles.searchText}>{t('home_search_placeholder')}</p>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 15L21 21M10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10C17 13.866 13.866 17 10 17Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        {/* Recommended Content */}
        <ContentSection
          label={isLoading ? t('home_loading') : t('home_recommended_contents')}
          bg="bg-soori-primary"
          cards={recommendedCards}
        />

        {/* Recent Records */}
        <ContentSection
          label={t('home_recent_records')}
          bg="bg-bg-softdark"
          cards={recentCards}
        />

      </div>

      {/* Bottom Nav */}
      <BottomNav activeTab="Home" />

    </Layout>
  )
}

export default HomePage;
