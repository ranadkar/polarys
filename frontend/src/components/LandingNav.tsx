import ThemeToggle from './ThemeToggle';
import styles from '../styles/LandingNav.module.scss';
import { useNavigate } from 'react-router-dom';

const LandingNav = () => {
    const navigate = useNavigate();
    return (
        <header className={styles.header}>
            <div className={styles.container}>
                <div className={styles.logoWrapper}>
                    <div className={styles.logoIcon} onClick={() => navigate('/')}>
                        <span className="material-symbols-outlined">balance</span>
                    </div>
                    <span className={styles.logoText} onClick={() => navigate('/')}>Polarys.</span>
                </div>
                <nav className={styles.nav}>
                    <a className={styles.navLink} href="#methodology">Methodology</a>
                    <a className={styles.navLink} href="#conservative">Viewpoints</a>
                    <a className={styles.navLink} href="#challenge">Verification</a>
                    <a className={styles.navLink} href="#synthesis">Synthesis</a>
                </nav>
                <div className={styles.actions}>
                    <ThemeToggle />
                    <button className={styles.mobileMenuButton}>
                        <span className="material-symbols-outlined">menu</span>
                    </button>
                </div>
            </div>
        </header>
    );
};

export default LandingNav;
