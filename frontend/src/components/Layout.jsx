function Layout({ children, className = "" }) {
  return (
    <div className={`bg-bg min-h-screen px-9 py-13 overflow-hidden relative ${className}`}>
      {children}
    </div>
  )
}




export default Layout;
