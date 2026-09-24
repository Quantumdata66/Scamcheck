import './howitworks.css';

export default function HowItWorks() {
  const cards = [
    {
      number: '01',
      heading: 'Paste',
      body: 'Copy the suspicious message and paste it into the checker.',
    },
    {
      number: '02',
      heading: 'Check',
      body: 'ScamCheck looks for patterns associated with supported scam types.',
    },
    {
      number: '03',
      heading: 'Understand',
      body: 'See what was detected and what you should verify before acting.',
    },
  ];

  return (
    <section className='howitworks' id='how-it-works'>
      <div className='text'>
        <h5>HOW IT WORKS</h5>
        <h3>Simple enough to use when you're unsure.</h3>
        <p>
          No complicated process. Paste the message, check it, then see what
          caught our attention.
        </p>
      </div>

      <div className='cards'>
        {cards.map((cardContent) => (
          <div className='card' key={cardContent.number}>
            <h5>{cardContent.number}</h5>
            <h4>{cardContent.heading}</h4>
            <p>{cardContent.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
