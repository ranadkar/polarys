import { Link } from 'react-router-dom';
import styles from '../styles/Nav.module.scss';

const Nav = () => {
  return (
    <nav className={styles.nav}>
      <Link to="/">Landing</Link>
      <Link to="/search-results">Search Results</Link>
    </nav>
  );
};

export default Nav;
