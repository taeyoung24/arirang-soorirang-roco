import { useEffect, useState } from 'react'
import { getSavedWords, resolveAssetUrl } from 'src/api'
import BottomNav from 'src/components/BottomNav'
import Layout from 'src/components/Layout'
import { HomeTopContainer } from 'src/components/TopContainer'
import mascot from 'src/assets/landing-mascot.svg'

function SavedWordCard({ word, image }) {
  return (
    <div className="w-[124px] h-[166px] bg-bg rounded-[20px] outline outline-[2.40px] outline-offset-[-1.20px] outline-text inline-flex flex-col justify-center items-center overflow-hidden">
      <div className="self-stretch h-9 px-1 flex items-center justify-center text-text text-base font-extrabold font-sans text-center leading-none">
        {word}
      </div>
      <div className="self-stretch border-t-[2.40px] border-text" />
      <img
        src={image}
        alt={word}
        className="self-stretch flex-1 min-h-0 object-cover bg-yellow-primary"
      />
    </div>
  )
}

function SavesPage() {
  const [savedWords, setSavedWords] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadSavedWords() {
      try {
        const data = await getSavedWords()

        if (!isMounted) return

        setSavedWords(data)
        setErrorMessage('')
      } catch (error) {
        if (!isMounted) return

        console.error('저장 단어를 불러오지 못했습니다:', error)
        setErrorMessage(error.message)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadSavedWords()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <Layout className="h-[770px] pb-24">
      <div className="w-80 min-h-[718px] mx-auto flex flex-col justify-start items-center gap-4">
        <HomeTopContainer mascotSrc={mascot} onHelp={() => { }} />

        <h1 className="self-stretch text-text text-2xl font-extrabold font-sans">
          저장 단어
        </h1>

        {isLoading && (
          <div className="self-stretch flex-1 flex justify-center items-center text-text text-lg font-extrabold font-sans">
            불러오는 중
          </div>
        )}

        {!isLoading && errorMessage && (
          <div className="self-stretch flex-1 flex justify-center items-center text-center text-ari-primary text-base font-semibold font-sans">
            {errorMessage}
          </div>
        )}

        {!isLoading && !errorMessage && (
          <div className="self-stretch grid grid-cols-2 gap-3">
            {savedWords.map((item) => (
              <SavedWordCard
                key={item.saved_word_id}
                word={item.word}
                image={resolveAssetUrl(item.image_url)}
              />
            ))}
          </div>
        )}
      </div>

      <BottomNav activeTab="Heart" />
    </Layout>
  )
}

export default SavesPage;
