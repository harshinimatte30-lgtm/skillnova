import { ReactNode } from 'react';
import { LogOut, Sparkles } from 'lucide-react';
import { User, Role } from '../types';

const nav: Record<Role, string[]> = {
  student: [
    'Dashboard', 'My Profile', 'My Skills', 'Assessment', 'Skill Gap',
    'Learning', 'Career Paths', 'Internships', 'Opportunities', 'Applications', 'Portfolio',
  ],
  company: [
    'Dashboard', 'Company Profile', 'Post Opportunity', 'Opportunities',
    'Candidate Matching', 'Internships', 'Faculty Programs', 'Create Faculty Program', 'Applications', 'Collaborations',
  ],
  academician: [
    'Dashboard', 'Profile', 'Verification Queue', 'Students',
    'Faculty Opportunities', 'Create Faculty Opportunity', 'Post Research/Project', 'Opportunities', 'Matched Students', 'Applications', 'Collaborations',
  ],
  admin: [
    'Admin Dashboard', 'Students', 'Skill Analytics', 'Placements',
    'Company Verification', 'Users', 'Companies', 'Academicians', 'Skills',
    'Opportunities', 'Analytics',
  ],
};

export default function Layout({
  user, page, setPage, children, onLogout,
}: {
  user: User;
  page: string;
  setPage: (p: string) => void;
  children: ReactNode;
  onLogout: () => void;
}) {
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <div className="logo"><Sparkles size={18} /></div>
          <span>SkillNova</span>
        </div>
        <div className="role-pill">{user.role}</div>
        <nav>
          {nav[user.role].map((x) => (
            <button className={page === x ? 'active' : ''} onClick={() => setPage(x)} key={x}>
              {x}
            </button>
          ))}
        </nav>
        <button className="logout" onClick={onLogout}>
          <LogOut size={16} />
          Log out
        </button>
      </aside>
      <main>
        <header>
          <div>
            <div className="eyebrow">AYUSH academia–industry skill intelligence</div>
            <h1>{page}</h1>
          </div>
          <div className="account">
            <span>{user.name || user.email}</span>
            <span className="avatar">{(user.name || user.email)[0]?.toUpperCase()}</span>
          </div>
        </header>
        <section className="content">{children}</section>
      </main>
    </div>
  );
}
