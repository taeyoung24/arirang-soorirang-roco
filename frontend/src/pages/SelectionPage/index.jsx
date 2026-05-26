import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCategories, getCategorySets } from 'src/api'
import Layout from 'src/components/Layout'
import { SearchTopContainer } from 'src/components/TopContainer'
import styles from './SelectionPage.module.css'

const FilterChip = ({ label, active, onClick }) => (
  <div
    className={`${styles.filterChip} ${active ? styles.filterChipActive : styles.filterChipInactive}`}
    onClick={onClick}
  >
    <div className={styles.filterChipLabel}>{label}</div>
  </div>
)

const ResultItem = ({ label, hasBorderTop, onClick }) => (
  <div className={`${styles.resultItem} ${hasBorderTop ? styles.resultItemBorderTop : ''}`} onClick={onClick}>
    <div className={styles.resultItemLabel}>{label}</div>
  </div>
)


const ResultSection = ({ title, items, onItemClick }) => {
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
            <ResultItem
              key={`${item.set_id}-${item.word}`}
              label={item.word}
              hasBorderTop={index > 0}
              onClick={() => onItemClick && onItemClick(item)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function SelectionPage() {
  const navigate = useNavigate()
  const [isExiting, setIsExiting] = useState(false)
  const [categories, setCategories] = useState([])
  const [setsByCategory, setSetsByCategory] = useState({})
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([])
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  const handleTransition = (path, bgColor) => {
    setIsExiting(true)
    if (bgColor) {
      document.body.style.backgroundColor = bgColor
    }
    setTimeout(() => navigate(path), 500)
  }

  useEffect(() => {
    let isMounted = true

    async function loadSelectionData() {
      try {
        const categoryList = await getCategories()
        const entries = await Promise.all(
          categoryList.map(async (category) => [
            category.category_id,
            await getCategorySets(category.category_id),
          ])
        )

        if (!isMounted) return

        setCategories(categoryList)
        setSetsByCategory(Object.fromEntries(entries))
        setSelectedCategoryIds(categoryList.map((category) => category.category_id))
      } catch (error) {
        console.error('카테고리/세트 정보를 불러오지 못했습니다:', error)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadSelectionData()

    return () => {
      isMounted = false
    }
  }, [])

  const toggleCategory = (categoryId) => {
    setSelectedCategoryIds((current) => {
      if (current.includes(categoryId)) {
        return current.filter((id) => id !== categoryId)
      }
      return [...current, categoryId]
    })
  }

  const results = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    return categories
      .filter((category) => selectedCategoryIds.includes(category.category_id))
      .map((category) => {
        const sets = setsByCategory[category.category_id] || []
        const visibleSets = sets.filter((set) => set.word_count > 0)
        const filteredSets = normalizedQuery
          ? visibleSets.filter((set) => (
              set.title.toLowerCase().includes(normalizedQuery)
              || set.words.some((word) => word.toLowerCase().includes(normalizedQuery))
            ))
          : visibleSets

        const wordItems = filteredSets.flatMap((set) => (
          set.words.map((word) => ({
            set_id: set.set_id,
            word,
          }))
        ))

        return {
          category,
          items: wordItems,
        }
      })
      .filter((section) => section.items.length > 0)
  }, [categories, query, selectedCategoryIds, setsByCategory])


  return (
    <Layout className={`${styles.layout} ${isExiting ? styles.fadeOut : ''}`}>
      <div className={styles.mainContainer}>

        {/* Search Header */}
        <SearchTopContainer
          onBack={() => handleTransition('/home')}
          onSearch={(event) => setQuery(event.target.value)}
        />

        {/* Filter Chips */}
        <div className={styles.filterChipContainer}>
          {categories.map((category) => (
            <FilterChip
              key={category.category_id}
              label={category.name_ko}
              active={selectedCategoryIds.includes(category.category_id)}
              onClick={() => toggleCategory(category.category_id)}
            />
          ))}
        </div>

        {/* Results Area */}
        <div className={styles.resultsArea}>

          {isLoading ? (
            <div className={styles.noInfoText}>
              불러오는 중
            </div>
          ) : results.length > 0 ? (
            results.map((section) => (
              <ResultSection
                key={section.category.category_id}
                title={section.category.name_ko}
                items={section.items}
                onItemClick={(item) => handleTransition(`/ingame/${item.set_id}`, 'var(--color-yellow-primary)')}
              />
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
