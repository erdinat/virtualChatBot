import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { useAuthStore } from "./store/authStore";
import LoginPage from "./pages/LoginPage";
import StudentPage from "./pages/StudentPage";
import TeacherPage from "./pages/TeacherPage";
import DiagnosticPage from "./pages/DiagnosticPage";
import OnboardingPage from "./pages/OnboardingPage";
import SplashScreen from "./components/SplashScreen";

const qc = new QueryClient();

function ProtectedRoute({ children, requiredRole }: { children: React.ReactNode; requiredRole?: string }) {
  const { token, role } = useAuthStore();
  if (!token) return <Navigate to="/" replace />;
  if (requiredRole && role !== requiredRole) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function RootRedirect() {
  const { token, role, username } = useAuthStore();
  if (!token) return <LoginPage />;
  if (role === "teacher") return <Navigate to="/teacher" replace />;
  // Students go to diagnostic first if not done (checked via localStorage flag)
  const diagKey = `diagnostic_done_${username}`;
  const onboardingKey = `onboarding_done_${username}`;
  if (!localStorage.getItem(diagKey)) return <Navigate to="/diagnostic" replace />;
  if (!localStorage.getItem(onboardingKey)) return <Navigate to="/onboarding" replace />;
  return <Navigate to="/student" replace />;
}

export default function App() {
  const [splashDone, setSplashDone] = useState(false);

  const handleSplashComplete = () => setSplashDone(true);

  return (
    <QueryClientProvider client={qc}>
      {!splashDone && <SplashScreen onComplete={handleSplashComplete} />}
      {splashDone && (
        <BrowserRouter>
          <Toaster
            position="top-right"
            toastOptions={{
              style: { background: "#1e1a41", color: "#e7e2ff", border: "1px solid #474464" },
            }}
          />
          <Routes>
            <Route path="/" element={<RootRedirect />} />
            <Route
              path="/student"
              element={
                <ProtectedRoute requiredRole="student">
                  <StudentPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher"
              element={
                <ProtectedRoute requiredRole="teacher">
                  <TeacherPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/diagnostic"
              element={
                <ProtectedRoute requiredRole="student">
                  <DiagnosticPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute requiredRole="student">
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      )}
    </QueryClientProvider>
  );
}
