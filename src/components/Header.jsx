export default function Header() {
  return (
    <header>
      <div className="bar">
        <div className="logo"><i>🏛️</i>Civic Issue Matchmaker</div>
        <nav>
          <a href="#">Find issues</a>
          <a href="#">How it works</a>
          <button className="btn">Login</button>
        </nav>
      </div>
    </header>
  );
}
