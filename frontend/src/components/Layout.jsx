import React from 'react';
import styles from './Layout.module.css';

function Layout({ children, className = "" }) {
  return (
    <div className={`${styles.layout} ${className}`}>
      {children}
    </div>
  )
}




export default Layout;
