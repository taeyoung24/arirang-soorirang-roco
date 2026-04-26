import Layout from '../../components/Layout'
import mascot from '../../assets/landing-mascot.svg'
import searchIcon from '../../assets/search.svg'
import normalMascot from '../../assets/mascot/normal_mascot.png'
import winterMascot from '../../assets/mascot/winter_mascot.png'
import houseIcon from '../../assets/house.svg'
import playIcon from '../../assets/play.svg'
import heartIcon from '../../assets/heart.svg'

function ContentCard({ title, image }) {
  return (
    <div className="bg-bg rounded-card border-2 border-black overflow-hidden shrink-0 w-[30%]">
      <p className="text-center font-bold py-2 border-b-0 border-black text-sm">{title}</p>
      <img src={image} alt={title} className="w-full" />
    </div>
  )
}

function ContentSection({ label, bg, cards }) {
  return (
    <div className={`relative ${bg} rounded-card pt-9 pb-3.5 px-4 mt-4`}>
      <div className="absolute -top-4 left-4 bg-green-primary text-text font-bold px-5 py-2 rounded-full border-2 border-black text-[18px]">
        {label}
      </div>
      <div className="flex gap-2 overflow-x-auto scrollbar-none">
        {cards.map((card, i) => (
          <ContentCard key={i} title={card.title} image={card.image} />
        ))} 
      </div>
    </div>
  )
}

function HomePage() {
  return (
    <Layout>
      <div className="flex flex-col gap-4 pb-30">

        {/* Header */}
        <div className="flex items-center justify-between">
          <img src={mascot} alt="mascot" className="w-12" />
          <button className="w-12 h-12 rounded-full border-2 border-black flex items-center justify-center text-sm font-bold">
            ?
          </button>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-text">
          아리, 수리와 헷갈리는 단어를 학습하세요
        </h1>

        {/* Login Banner */}
        <div className="relative rounded-card border-2 border-black py-6 pl-4">
          <div className="absolute top-0 right-0 translate-x-1/3 -translate-y-1/2 w-14 h-14 rounded-full bg-[#7D7D7D] border-2 border-black" />
          <p className="font-bold text-text text-[20px]">로그인</p>
          <p className="text-[16px] text-text-dimmed">더 나은 학습을 위해 로그인하세요.</p>
        </div>

        {/* Search */}
        <div className="flex items-center justify-between bg-white-primary border-2 border-black rounded-hard py-3 px-5">
          <p className="text-[18px] text-text-light">대화 검색</p>
          <img src={searchIcon} alt="search" className="w-5 h-5" />
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
      <div className="fixed justify-between bottom-13 left-1/2 -translate-x-1/2 w-[186px] h-11 bg-yellow-primary rounded-full border-2 border-black flex items-center justify-around px-8">
        <img src={houseIcon} alt="home" className="w-8 h-8" />
        <img src={playIcon} alt="play" className="w-8 h-8" />
        <img src={heartIcon} alt="heart" className="w-8 h-8" />
      </div>
    </Layout>
  )
}

export default HomePage
