import { useNavigate } from 'react-router-dom'
import mascot from 'src/assets/landing-mascot.svg'
import normalMascot from 'src/assets/mascot/word-image-snow.png'
import winterMascot from 'src/assets/mascot/word-image-write.png'
import BottomNav from 'src/components/BottomNav'
import Layout from 'src/components/Layout'
import { HomeTopContainer } from 'src/components/TopContainer'


function ContentCard({ title, image }) {
  return (
    <div className="w-24 bg-bg rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex flex-col justify-center items-center overflow-hidden shrink-0 snap-start">
      <div className="self-stretch h-8 flex items-center justify-center text-text text-base font-semibold font-sans text-center">
        {title}
      </div>
      <div className="self-stretch border-t-[2.40px] border-text" />
      <img src={image} alt={title} className="self-stretch h-24 object-cover" />
    </div>
  )
}



function ContentSection({ label, bg, cards }) {
  return (
    <div className="PopAreaWrap self-stretch pt-5 relative inline-flex flex-col justify-end items-center gap-2.5">
      <div className={`Blob self-stretch h-44 pt-5 ${bg} rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-start items-center overflow-hidden`}>
        <div className="ContentList px-4 scroll-px-4 h-full flex justify-start items-center gap-[5px] overflow-x-auto scrollbar-none snap-x snap-mandatory">
          {cards.map((card, i) => (
            <ContentCard key={i} title={card.title} image={card.image} />
          ))}
        </div>
      </div>
      <div className="Frame1 h-11 px-5 left-[16px] top-0 absolute bg-green-primary rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-center items-center gap-2.5 overflow-hidden">
        <div className="text-text text-lg font-extrabold font-sans">{label}</div>
      </div>
    </div>
  )
}




function HomePage() {
  const navigate = useNavigate()

  return (
    <Layout className="h-[770px]">
      <div className="w-80 h-[718px] mx-auto flex flex-col justify-start items-center gap-4">

        {/* HomeTopContainer */}
        <HomeTopContainer mascotSrc={mascot} onHelp={() => { }} />



        {/* Title */}
        <h1 className="self-stretch justify-start text-text text-2xl font-extrabold font-sans">
          아리, 수리와 헷갈리는 단어를 학습하세요
        </h1>

        {/* Login Banner */}
        <div className="self-stretch px-4 py-4 relative bg-bg rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text flex flex-col justify-center items-center gap-1">
          <p className="self-stretch justify-start text-text text-xl font-extrabold font-sans">로그인</p>
          <p className="self-stretch justify-start text-text text-base font-semibold font-sans">더 나은 학습을 위해 로그인하세요.</p>
          <div className="left-[262px] top-[-26px] absolute">
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
          className="self-stretch h-12 px-5 bg-white-primary rounded-[32px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex justify-center items-center gap-4 overflow-hidden cursor-pointer active:scale-95 transition-all"
        >
          <p className="flex-1 justify-start text-text-light text-lg font-extrabold font-sans">대화 검색</p>
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

