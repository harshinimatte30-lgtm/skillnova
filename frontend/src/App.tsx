import { useState } from 'react';

import Auth from './pages/Auth';
import Student from './pages/Student';
import Org from './pages/Org';
import Academician from './pages/Academician';
import Admin from './pages/Admin';

import Layout from './components/Layout';

import { User } from './types';

import './styles.css';

const DEFAULT_PAGES: Record<User['role'], string> = {
  student: 'Dashboard',
  company: 'Dashboard',
  academician: 'Dashboard',
  admin: 'Admin Dashboard',
};

export default function App() {
  /*
   * ------------------------------------------------------------
   * USER / AUTH STATE
   * ------------------------------------------------------------
   *
   * We keep the logged-in user in localStorage so refreshing the
   * browser does not immediately log the user out.
   */

  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('skillnova_user');

    if (!savedUser) {
      return null;
    }

    try {
      return JSON.parse(savedUser) as User;
    } catch {
      localStorage.removeItem('skillnova_user');
      return null;
    }
  });

  /*
   * ------------------------------------------------------------
   * CURRENT PAGE
   * ------------------------------------------------------------
   *
   * Layout owns the visible navigation.
   * Each role has its own navigation list inside Layout.tsx.
   */

  const [page, setPage] = useState<string>(() => {
    if (!user) {
      return 'Dashboard';
    }

    return DEFAULT_PAGES[user.role];
  });

  /*
   * ------------------------------------------------------------
   * LOGIN
   * ------------------------------------------------------------
   */

  function handleLogin(loggedInUser: User) {
    localStorage.setItem(
      'skillnova_user',
      JSON.stringify(loggedInUser),
    );

    setUser(loggedInUser);
    setPage(DEFAULT_PAGES[loggedInUser.role]);
  }

  /*
   * ------------------------------------------------------------
   * LOGOUT
   * ------------------------------------------------------------
   */

  function handleLogout() {
    localStorage.removeItem('skillnova_user');
    localStorage.removeItem('skillnova_token');

    setUser(null);
    setPage('Dashboard');
  }

  /*
   * ------------------------------------------------------------
   * AUTH SCREEN
   * ------------------------------------------------------------
   */

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  /*
   * ------------------------------------------------------------
   * MAIN APPLICATION
   * ------------------------------------------------------------
   *
   * IMPORTANT:
   *
   * Layout is the parent of every role portal.
   * Therefore the sidebar is always rendered here.
   *
   * The actual functionality remains inside:
   *
   * Student.tsx
   * Org.tsx
   * Academician.tsx
   * Admin.tsx
   */

  return (
    <Layout
      user={user}
      page={page}
      setPage={setPage}
      onLogout={handleLogout}
    >
      {user.role === 'student' && (
        <Student
          page={page}
          setPage={setPage}
        />
      )}

      {user.role === 'company' && (
        <Org
          role="company"
          page={page}
          setPage={setPage}
          userId={user.id}
        />
      )}

      {user.role === 'academician' && (
        <Academician
          page={page}
          setPage={setPage}
          userId={user.id}
        />
      )}

      {user.role === 'admin' && (
        <Admin
          page={page}
          setPage={setPage}
        />
      )}
    </Layout>
  );
}