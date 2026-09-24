import './footer.css';

export default function Footer() {
  return (
    <>
      <footer className='footer'>
        <div className='footer-brand'>
          <h2>ScamCheck</h2>
          <p>
            A simple tool for checking suspicious messages <br />
            and understanding possible scam indicators.
          </p>
        </div>

        <ul className='footer-links'>
          <li>
            <a href='#how-it-works'>How it works</a>
          </li>
          <li>
            <a href='#about'>About</a>
          </li>
          <li>
            <a href='#faq'>FAQ</a>
          </li>
        </ul>
      </footer>
    </>
  );
}
