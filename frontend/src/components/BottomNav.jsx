import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './BottomNav.module.css';

const BottomNav = ({ activeTab = "Home" }) => {
  const navigate = useNavigate();

  return (
    <div className={styles.container}>
      <div 
        data-layer="bottom-nav" 
        data-select={activeTab} 
        className={styles.nav}
      >
        {/* House Icon */}
        <div 
          data-layer="Navigation / House_01" 
          onClick={() => navigate('/home')}
          className={styles.iconWrapper}
        >
          <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M25 21.2502V14.3153C25 13.6474 24.9994 13.3132 24.9182 13.0024C24.8462 12.727 24.7281 12.4663 24.5682 12.2308C24.3878 11.965 24.1369 11.7446 23.6343 11.3048L17.6343 6.05478C16.701 5.23818 16.2344 4.83008 15.7092 4.67478C15.2465 4.53793 14.7533 4.53793 14.2905 4.67478C13.7658 4.82996 13.2998 5.23767 12.368 6.05305L6.36597 11.3048C5.8633 11.7446 5.61255 11.965 5.43213 12.2308C5.27224 12.4663 5.15319 12.727 5.08121 13.0024C5 13.3132 5 13.6474 5 14.3153V21.2502C5 22.4151 5 22.9973 5.1903 23.4567C5.44404 24.0693 5.9304 24.5565 6.54297 24.8103C7.0024 25.0006 7.58482 25.0006 8.74968 25.0006C9.91453 25.0006 10.4976 25.0006 10.957 24.8103C11.5696 24.5565 12.0558 24.0694 12.3096 23.4568C12.4999 22.9974 12.5 22.4149 12.5 21.2501V20.0001C12.5 18.6194 13.6193 17.5001 15 17.5001C16.3807 17.5001 17.5 18.6194 17.5 20.0001V21.2501C17.5 22.4149 17.5 22.9974 17.6903 23.4568C17.944 24.0694 18.4304 24.5565 19.043 24.8103C19.5024 25.0006 20.0848 25.0006 21.2497 25.0006C22.4145 25.0006 22.9976 25.0006 23.457 24.8103C24.0696 24.5565 24.5558 24.0693 24.8096 23.4567C24.9999 22.9973 25 22.4151 25 21.2502Z" fill={activeTab === "Home" ? "var(--text, #2C2C2C)" : "none"} stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        {/* Play Icon */}
        <div 
          data-layer="Media / Play" 
          onClick={() => navigate('/ingame')}
          className={styles.iconWrapper}
        >
          <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6.25 21.6671V8.33373C6.25 7.23427 6.25 6.68393 6.48137 6.35863C6.6833 6.07471 6.99455 5.8883 7.34009 5.84374C7.73585 5.79269 8.22126 6.05157 9.19067 6.56859L21.6907 13.2353L21.6952 13.2373C22.7665 13.8086 23.3024 14.0945 23.4782 14.4754C23.6316 14.8077 23.6316 15.1913 23.4782 15.5237C23.3022 15.9052 22.765 16.1921 21.6907 16.7651L9.19067 23.4318C8.22056 23.9492 7.736 24.2071 7.34009 24.156C6.99455 24.1114 6.6833 23.9251 6.48137 23.6411C6.25 23.3158 6.25 22.7665 6.25 21.6671Z" fill={activeTab === "Play" ? "var(--text, #2C2C2C)" : "none"} stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        {/* Heart Icon */}
        <div 
          data-layer="Interface / Heart_02" 
          onClick={() => navigate('/saves')}
          className={styles.iconWrapper}
        >
          <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M24.0466 7.79664C25.9799 9.72994 26.054 12.8408 24.2148 14.8639L14.9994 25.0001L5.78515 14.8639C3.94599 12.8408 4.02006 9.72987 5.95336 7.79657C8.11201 5.63792 11.6672 5.83518 13.5742 8.219L15 10.0006L16.4246 8.2188C18.3316 5.83497 21.888 5.63799 24.0466 7.79664Z" fill={activeTab === "Heart" ? "var(--text, #2C2C2C)" : "none"} stroke="var(--text, #2C2C2C)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
    </div>
  );
};

export default BottomNav;
