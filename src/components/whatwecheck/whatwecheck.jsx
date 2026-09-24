import './whatwecheck.css';

export default function WhatWeCheck() {
  return (
    <>
      <section className='what-we-check' id='about'>
        <div className='check-intro'>
          <h4>WHAT WE CHECK</h4>

          <h2>
            Focused on common <br />
            scam messages.
          </h2>

          <p>
            The first version focuses on suspicious text involving a few
            specific categories.
          </p>
        </div>

        <div className='check-cards'>
          <div className='check-card'>
            <div className='card-header'>
              <img
                src='https://unpkg.com/lucide-static@latest/icons/landmark.svg'
                alt='Bank'
                className='card-icon'
              />
              <h3>Bank & payment scams</h3>
            </div>
            <p>
              Detects urgent requests for money transfers, fake transaction
              alerts, and unauthorized account access warnings.
            </p>
          </div>

          <div className='check-card'>
            <div className='card-header'>
              <img
                src='https://unpkg.com/lucide-static@latest/icons/briefcase.svg'
                alt='Job'
                className='card-icon'
              />
              <h3>Fake job offers</h3>
            </div>
            <p>
              Identifies unrealistically high salary claims, immediate hiring
              promises, and upfront equipment fee requests.
            </p>
          </div>

          <div className='check-card'>
            <div className='card-header'>
              <img
                src='https://unpkg.com/lucide-static@latest/icons/trending-up.svg'
                alt='Investment'
                className='card-icon'
              />
              <h3>Investment scams</h3>
            </div>
            <p>
              Flags guaranteed return promises, high-pressure crypto schemes,
              and time-sensitive opportunity claims.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
