import { useState } from 'react';
import Auth from './pages/Auth';
import Student from './pages/Student';
import Org from './pages/Org';
import Academician from './pages/Academician';
import Admin from './pages/Admin';
import Layout from './components/Layout';
import { User } from './types';
import './styles.css';

const defaults: Record<User['role'], string> = {
  student: 'Dashboard',
  company: 'Dashboard',
  academician: 'Dashboard',
  admin: 'Admin Dashboard',
};

export default function App() {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem('skillnova_user');

    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw);
    } catch {
      localStorage.removeItem('skillnova_user');
      return null;
    }
  });

  const [page, setPage] = useState<string>(
    user ? defaults[user.role] : 'Dashboard'
  );

  function login(u: User) {
    localStorage.setItem('skillnova_user', JSON.stringify(u));
    setUser(u);
    setPage(defaults[u.role]);
  }

  function logout() {
    localStorage.removeItem('skillnova_user');
    localStorage.removeItem('skillnova_token');

    setUser(null);
    setPage('Dashboard');
  }

  if (!user) {
    return <Auth onLogin={login} />;
  }

  return (
    <Layout
      user={user}
      page={page}
      setPage={setPage}
      onLogout={logout}
    >
      {user.role === 'student' ? (
        <Student
          page={page}
          setPage={setPage}
        />
      ) : user.role === 'company' ? (
        <Org
          role="company"
          page={page}
          setPage={setPage}
          userId={user.id}
        />
      ) : user.role === 'academician' ? (
        <Academician
          page={page}
          setPage={setPage}
          userId={user.id}
        />
      ) : (
        <Admin
          page={page}
        />
      )}
    </Layout>
  );
}