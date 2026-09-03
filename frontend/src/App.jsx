import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import TopBar from './components/TopBar';
import NavRail from './components/NavRail';
import ToastContainer from './components/ToastContainer';
import CommandPalette from './components/CommandPalette';
import ConsoleView from './components/views/ConsoleView';
import ChatHubView from './components/views/ChatHubView';
import PipelineView from './components/views/PipelineView';
import StudyLabView from './components/views/StudyLabView';
import DevSystemView from './components/views/DevSystemView';

function MainLayout() {
  const { currentView } = useApp();

  return (
    <div className="bg-[#F8FAFC] text-[#0F172A] flex flex-col h-screen overflow-hidden text-[13px]">
      <TopBar />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <NavRail />

        <main className="flex-1 flex flex-col min-w-0 bg-[#F8FAFC] overflow-hidden">
          {currentView === 'console' && <ConsoleView />}
          {currentView === 'chat' && <ChatHubView />}
          {currentView === 'pipeline' && <PipelineView />}
          {currentView === 'study' && <StudyLabView />}
          {currentView === 'dev' && <DevSystemView />}
        </main>
      </div>

      <ToastContainer />
      <CommandPalette />
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
}
