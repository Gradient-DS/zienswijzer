import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { queryClient } from './api/client';
import { RootLayout, AuthLayout, WorkspaceLayout } from './layouts';
import LoginPage from './pages/LoginPage';
import WorkspacePage from './pages/WorkspacePage';
import HomePage from './pages/HomePage';
import HomePlaceholder from './pages/HomePlaceholder';
import CaseDetailPage from './pages/CaseDetailPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<RootLayout />}>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
            </Route>

            <Route element={<WorkspaceLayout />}>
              <Route path="/workspaces" element={<WorkspacePage />} />

              <Route element={<HomePage />}>
                <Route path="/home" element={<HomePlaceholder />} />
                <Route path="/cases/:id" element={<CaseDetailPage />} />
              </Route>
            </Route>

            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
