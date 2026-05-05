import { useNavigate } from 'react-router-dom'
import mascot from 'src/assets/landing-mascot.svg'
import normalMascot from 'src/assets/mascot/word-image-snow.png'
import winterMascot from 'src/assets/mascot/word-image-write.png'
import BottomNav from 'src/components/BottomNav'
import Layout from 'src/components/Layout'
import { HomeTopContainer } from 'src/components/TopContainer'
import styles from './HomePage.module.css'


function ContentCard({ title, image }) {
  return (
    <div className={styles.contentCard}>
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
            <ContentCard key={i} title={card.title} image={card.image} />
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

  return (
    <Layout className={styles.layout}>
      <div className={styles.mainContainer}>

        {/* HomeTopContainer */}
        <HomeTopContainer mascotSrc={mascot} onHelp={() => { }} />



        {/* Title */}
        <h1 className={styles.title}>
          아리, 수리와 헷갈리는 단어를 학습하세요
        </h1>

        {/* Login Banner */}
        <div className={styles.loginBanner}>
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
        </div>

        {/* Search */}
        <div
          onClick={() => navigate('/selection')}
          className={styles.searchBox}
        >

          <p className={styles.searchText}>대화 검색</p>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 15L21 21M10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10C17 13.866 13.866 17 10 17Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        {/* Recommended Content */}
        <ContentSection
          label="추천 컨텐츠"
          bg="bg-soori-primary"
          cards={[
            { title: '병원', image: normalMascot },
            { title: '고등학교', image: winterMascot },
            { title: '은행', image: normalMascot },
            { title: '학교', image: winterMascot },
          ]}
        />

        {/* Recent Records */}
        <ContentSection
          label="최근 기록"
          bg="bg-bg-softdark"
          cards={[
            { title: '쓰다', image: normalMascot },
            { title: '눈', image: winterMascot },
            { title: '쓰다', image: normalMascot },
            { title: '바람', image: winterMascot },
          ]}
        />

      </div>

      {/* Bottom Nav */}
      <BottomNav activeTab="Home" />

    </Layout>
  )
}

export default HomePage;

