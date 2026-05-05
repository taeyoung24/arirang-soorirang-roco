import React from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from 'src/components/Layout'
import { SearchTopContainer } from 'src/components/TopContainer'
import styles from './SelectionPage.module.css'

const FilterChip = ({ label, active }) => (
  <div className={`${styles.filterChip} ${active ? styles.filterChipActive : styles.filterChipInactive}`}>
    <div className={styles.filterChipLabel}>{label}</div>
  </div>
)

const ResultItem = ({ label, hasBorderTop }) => (
  <div className={`${styles.resultItem} ${hasBorderTop ? styles.resultItemBorderTop : ''}`}>
    <div className={styles.resultItemLabel}>{label}</div>
  </div>
)


const ResultSection = ({ title, items }) => {
  const [isOpen, setIsOpen] = React.useState(true);
  const count = items.length;

  return (
    <div className={styles.resultSection}>
      <div 
        className={styles.resultSectionHeader}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className={styles.resultSectionTitle}>{title} ({count})</div>
        <div className={`${styles.iconWrapper} ${isOpen ? '' : styles.iconRotated}`}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 10L12 14L8 10" stroke="var(--text, #2C2C2C)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
      {isOpen && (
        <div className={styles.resultSectionContent}>
          {items.map((item, index) => (
            <ResultItem key={index} label={item} hasBorderTop={index > 0} />
          ))}
        </div>
      )}
    </div>
  )
}

export default function SelectionPage() {
  const navigate = useNavigate()

  // 임시 데이터 (실제 연동 시 상태로 관리)
  const results = [
    { title: "고등학교", items: ["쓰다", "눈"] },
    { title: "병원", items: ["쓰다", "맞다", "내리다", "나다", "보다"] }
  ]


  return (
    <Layout className={styles.layout}>
      <div className={styles.mainContainer}>

        {/* Search Header */}
        <SearchTopContainer onBack={() => navigate('/home')} onSearch={() => { }} />

        {/* Filter Chips */}
        <div className={styles.filterChipContainer}>
          <FilterChip label="병원" active={true} />
          <FilterChip label="고등학교" active={true} />
          <FilterChip label="Hanging with" active={false} />
          <FilterChip label="은행" active={false} />
          <FilterChip label="카페" active={false} />
          <FilterChip label="PC 게임" active={false} />
          <FilterChip label="대학교" active={false} />
        </div>

        {/* Results Area */}
        <div className={styles.resultsArea}>

          {results.length > 0 ? (
            results.map((section, idx) => (
              <ResultSection key={idx} title={section.title} count={section.count} items={section.items} />
            ))
          ) : (
            <div className={styles.noInfoText}>
              정보 없음
            </div>
          )}
        </div>



      </div>
    </Layout>
  )
}

