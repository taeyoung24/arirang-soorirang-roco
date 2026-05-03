import React from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from 'src/components/Layout'
import { SearchTopContainer } from 'src/components/TopContainer'

const FilterChip = ({ label, active }) => (
  <div className={`px-2.5 py-1 ${active ? 'bg-yellow-primary' : 'bg-bg'} rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-center items-center gap-4 overflow-hidden cursor-pointer active:scale-95 transition-all`}>
    <div className="justify-start text-text text-base font-semibold font-sans">{label}</div>
  </div>
)

const ResultItem = ({ label, hasBorderTop }) => (
  <div className={`self-stretch h-11 ${hasBorderTop ? 'border-t-[2.40px] border-text' : ''} flex justify-center items-center gap-2.5 cursor-pointer hover:bg-black/5 active:bg-black/10 transition-colors`}>
    <div className="text-center justify-start text-text text-base font-semibold font-sans">{label}</div>
  </div>
)

const ResultSection = ({ title, count, items }) => (
  <div className="self-stretch rounded-[20px] flex flex-col justify-start items-start gap-2.5">
    <div className="self-stretch px-0.5 inline-flex justify-between items-center">
      <div className="text-center justify-start text-text text-base font-semibold font-sans">{title} ({count})</div>
      <div className="relative">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M16 10L12 14L8 10" stroke="var(--color-text, #2C2C2C)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
    </div>
    <div className="self-stretch rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text flex flex-col">
      {items.map((item, index) => (
        <ResultItem key={index} label={item} hasBorderTop={index > 0} />
      ))}
    </div>
  </div>
)

export default function SelectionPage() {
  const navigate = useNavigate()

  return (
    <Layout className="bg-bg h-[770px] !overflow-visible">
      <div className="w-80 h-[718px] mx-auto flex flex-col justify-start items-center gap-4">
        
        {/* Search Header */}
        <SearchTopContainer onBack={() => navigate('/home')} onSearch={() => {}} />

        {/* Filter Chips */}
        <div className="self-stretch inline-flex justify-start items-start gap-2.5 flex-wrap content-start">
          <FilterChip label="병원" active={true} />
          <FilterChip label="고등학교" active={true} />
          <FilterChip label="Hanging with" active={false} />
          <FilterChip label="은행" active={false} />
          <FilterChip label="카페" active={false} />
          <FilterChip label="PC 게임" active={false} />
          <FilterChip label="대학교" active={false} />
        </div>

        {/* Results Area */}
        <div className="ResultsArea self-stretch inline-flex flex-col justify-start items-center gap-4 overflow-y-auto scrollbar-none py-2 px-[1.2px]">
          <ResultSection title="고등학교" count={2} items={["쓰다", "눈"]} />
          <ResultSection title="병원" count={5} items={["쓰다", "맞다", "내리다", "나다", "보다"]} />
        </div>

      </div>
    </Layout>
  )
}
