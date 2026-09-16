import { useState } from 'react';
import { Header } from './components/Header';
import { AuthModal } from './components/AuthModal';
import { MeetingsView } from './views/MeetingsView';
import { ProjectsView } from './views/ProjectsView';
import { TemplatesView } from './views/TemplatesView';
import { AuthProvider } from './lib/auth';
import { ToastProvider } from './lib/toast';

function AppInner() {
  const [activeTab, setActiveTab] = useState('meetings');
  const [authModalOpen, setAuthModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-paper">
      <Header activeTab={activeTab} onTabChange={setActiveTab} onOpenAuth={() => setAuthModalOpen(true)} />

      {activeTab === 'meetings' && <MeetingsView />}
      {activeTab === 'projects' && <ProjectsView />}
      {activeTab === 'templates' && <TemplatesView />}

      {authModalOpen && <AuthModal onClose={() => setAuthModalOpen(false)} />}
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppInner />
      </AuthProvider>
    </ToastProvider>
  );
}