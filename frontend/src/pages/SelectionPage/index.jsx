import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCategories, getCategorySets } from 'src/api'
import Layout from 'src/components/Layout'
import { SearchTopContainer } from 'src/components/TopContainer'

const FilterChip = ({ label, active, onClick }) => (
  <div
    onClick={onClick}
    className={`px-2.5 py-1 ${active ? 'bg-yellow-primary' : 'bg-bg'} rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-center items-center gap-4 overflow-hidden cursor-pointer active:scale-95 transition-all`}
  >
    <div className="justify-start text-text text-base font-semibold font-['Pretendard'] leading-none">{label}</div>
  </div>
)

const ResultItem = ({ label, hasBorderTop, onClick }) => (
  <div
    onClick={onClick}
    className={`self-stretch h-11 px-3 ${hasBorderTop ? 'border-t-[2.40px] border-text' : ''} flex justify-center items-center gap-2.5 cursor-pointer hover:bg-black/5 active:bg-black/10 transition-colors`}
  >


    <div className="text-center justify-start text-text text-base font-semibold font-['Pretendard'] select-text">{label}</div>
  </div>
)


const ResultSection = ({ title, items, onSelect }) => {
  const [isOpen, setIsOpen] = React.useState(true);
  const count = items.length;

  return (
    <div className="self-stretch rounded-[20px] flex flex-col justify-start items-start gap-2.5">
      <div 
        className="self-stretch px-0.5 inline-flex justify-between items-center cursor-pointer active:opacity-70 transition-all"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="text-center justify-start text-text text-base font-semibold font-['Pretendard']">{title} ({count})</div>
        <div className={`relative transition-transform duration-200 ${isOpen ? '' : '-rotate-90'}`}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 10L12 14L8 10" stroke="var(--text, #2C2C2C)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
      {isOpen && (
        <div className="self-stretch rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text flex flex-col justify-center items-center overflow-hidden">
          {items.map((item, index) => (
            <ResultItem
              key={`${item.set_id}-${item.word}`}
              label={item.word}
              hasBorderTop={index > 0}
              onClick={() => onSelect(item.set_id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function SelectionPage() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState([])
  const [setsByCategory, setSetsByCategory] = useState({})
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([])
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)

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
    <Layout className="bg-bg min-h-screen pb-24">
      <div className="w-80 min-h-[718px] mx-auto flex flex-col justify-start items-center gap-4">

        {/* Search Header */}
        <SearchTopContainer
          onBack={() => navigate('/home')}
          onSearch={(event) => setQuery(event.target.value)}
        />

        {/* Filter Chips */}
        <div className="self-stretch inline-flex justify-start items-start gap-2.5 flex-wrap content-start">
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
        <div className="ResultsArea self-stretch flex-1 flex flex-col justify-start items-center gap-4">

          {isLoading ? (
            <div className="self-stretch text-center justify-start text-text-dimmed text-lg font-semibold font-['Pretendard']">
              불러오는 중
            </div>
          ) : results.length > 0 ? (
            results.map((section) => (
              <ResultSection
                key={section.category.category_id}
                title={section.category.name_ko}
                items={section.items}
                onSelect={(setId) => navigate(`/ingame/${setId}`)}
              />
            ))
          ) : (
            <div className="self-stretch text-center justify-start text-text-dimmed text-lg font-semibold font-['Pretendard']">
              정보 없음
            </div>
          )}
        </div>



      </div>
    </Layout>
  )
}
