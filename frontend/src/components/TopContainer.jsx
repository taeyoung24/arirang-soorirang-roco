import React from 'react';
import { SimpleIconButton } from './Button';
import styles from './TopContainer.module.css';


export const IngameTopContainer = ({ onBack, onHelp, status = 'locked' }) => {
  const isLocked = status === 'locked';

  return (
    <div className={styles.container}>
      {/* Back Button */}
      <SimpleIconButton type="back" onClick={onBack} />



      {/* Stage Status */}
      <div className={styles.statusArea}>
        <div className={styles.iconWrapper}>
          {isLocked ? (
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7.6921 7.5H6.0002C5.06678 7.5 4.59972 7.5 4.2432 7.68166C3.9296 7.84144 3.67482 8.09623 3.51503 8.40983C3.33337 8.76635 3.33337 9.23341 3.33337 10.1668V14.8335C3.33337 15.7669 3.33337 16.2334 3.51503 16.5899C3.67482 16.9035 3.9296 17.1587 4.2432 17.3185C4.59938 17.5 5.06589 17.5 5.99749 17.5H14.0026C14.9342 17.5 15.4 17.5 15.7562 17.3185C16.0698 17.1587 16.3254 16.9035 16.4852 16.5899C16.6667 16.2337 16.6667 15.7679 16.6667 14.8363V10.1641C16.6667 9.23249 16.6667 8.766 16.4852 8.40983C16.3254 8.09623 16.0698 7.84144 15.7562 7.68166C15.3997 7.5 14.9336 7.5 14.0002 7.5H12.3075M7.6921 7.5H12.3075M7.6921 7.5C7.58589 7.5 7.50004 7.4139 7.50004 7.30769V5C7.50004 3.61929 8.61933 2.5 10 2.5C11.3808 2.5 12.5 3.61929 12.5 5V7.30769C12.5 7.4139 12.4137 7.5 12.3075 7.5" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7.50004 7.5H6.0002C5.06678 7.5 4.59972 7.5 4.2432 7.68166C3.9296 7.84145 3.67482 8.09623 3.51503 8.40983C3.33337 8.76635 3.33337 9.23341 3.33337 10.1668V14.8335C3.33337 15.7669 3.33337 16.2334 3.51503 16.5899C3.67482 16.9035 3.9296 17.1587 4.2432 17.3185C4.59938 17.5 5.06588 17.5 5.99749 17.5L14.0026 17.5C14.9342 17.5 15.4 17.5 15.7562 17.3185C16.0698 17.1587 16.3254 16.9035 16.4852 16.5899C16.6667 16.2337 16.6667 15.7679 16.6667 14.8363V10.1641C16.6667 9.23249 16.6667 8.766 16.4852 8.40983C16.3254 8.09623 16.0698 7.84144 15.7562 7.68166C15.3997 7.5 14.9336 7.5 14.0002 7.5H7.50004ZM7.50004 7.5V5.1001C7.50004 3.66416 8.58339 2.5 9.91977 2.5C10.6064 2.5 11.2257 2.80732 11.6661 3.30094" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </div>
        <div className={styles.statusText}>
          {isLocked ? "스테이지 잠김" : "스테이지 완료"}
        </div>
      </div>

      {/* Help Button */}
      <SimpleIconButton type="help" onClick={onHelp} />


    </div>
  );
};

export const SearchTopContainer = ({ onBack, onSearch }) => {
  return (
    <div className={styles.searchContainer}>
      {/* Back Button */}
      <SimpleIconButton type="back" onClick={onBack} />



      {/* Search Input Area */}
      <div className={styles.inputWrapper}>
        <input 
          type="text"
          placeholder="대화 검색"
          onChange={onSearch}
          className={styles.input}
        />
        <div className={styles.searchIconWrapper}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M15 15L21 21M10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10C17 13.866 13.866 17 10 17Z" stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export const HomeTopContainer = ({ mascotSrc, onHelp }) => {
  return (
    <div className={styles.homeContainer}>
      {/* Mascot Area */}
      <div className={styles.mascotWrapper}>
        <img src={mascotSrc} alt="mascot" className={styles.mascotImg} />
      </div>

      {/* Help Button */}
      <SimpleIconButton type="help" onClick={onHelp} />


    </div>
  );
};
