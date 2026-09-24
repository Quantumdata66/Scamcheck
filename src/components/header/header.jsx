import { useState } from 'react';
import './header.css';

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen((prev) => !prev);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  return (
    <header className='site-header'>
      <div className='header-brand'>
        <a href='#'>ScamCheck</a>
      </div>

      <nav className={`header-nav ${isMenuOpen ? 'is-open' : ''}`}>
        <ul className='nav-list'>
          <li>
            <a href='#how-it-works' onClick={closeMenu}>
              How it works
            </a>
          </li>
          <li>
            <a href='#about' onClick={closeMenu}>
              About
            </a>
          </li>
          <li>
            <a href='#faq' onClick={closeMenu}>
              FAQ
            </a>
          </li>
        </ul>

        <div className='nav-cta'>
          <a href='#check' className='btn-cta' onClick={closeMenu}>
            Check a message
          </a>
        </div>
      </nav>

      <button
        className='menu-toggle'
        onClick={toggleMenu}
        aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
        aria-expanded={isMenuOpen}
      >
        {isMenuOpen ? '✕' : '☰'}
      </button>
    </header>
  );
}
