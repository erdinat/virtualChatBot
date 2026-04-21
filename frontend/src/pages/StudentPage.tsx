import { motion, AnimatePresence } from "framer-motion";
import { getQuiz } from "../api/client";

import { useStudentPage } from "../hooks/useStudentPage";
import CurriculumGrid  from "../components/student/CurriculumGrid";
import ChatView        from "../components/student/ChatView";
import PreTestModal    from "../components/student/PreTestModal";
import QuizModal       from "../components/student/QuizModal";
import StudentSidebar, { getAvatarUrl } from "../components/student/StudentSidebar";
import { LEVEL_META } from "../components/student/types";

export default function StudentPage() {
  const pg = useStudentPage();

  const avatarUrl = getAvatarUrl(pg.username ?? null);
  const initials  = (pg.name ?? pg.username ?? "?")[0].toUpperCase();

  const sidebarContent = (
    <StudentSidebar
      name={pg.name ?? null}
      username={pg.username ?? null}
      activeView={pg.activeView}
      recentHistory={pg.recentHistory}
      nextTopic={pg.nextTopic}
      avgMastery={pg.avgMastery}
      avatarUrl={avatarUrl}
      initials={initials}
      onLogout={() => { pg.logout(); window.location.href = "/"; }}
    />
  );

  return (
    <div className="flex h-screen overflow-hidden bg-surface text-on-surface font-body">

      {/* Desktop sidebar */}
      <AnimatePresence initial={false}>
        {pg.desktopSidebar && (
          <motion.aside key="desktop-sidebar"
            initial={{ width: 0, opacity: 0 }} animate={{ width: 320, opacity: 1 }} exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="hidden md:flex h-full bg-surface-container border-r border-white/5 flex-col py-8 overflow-y-auto overflow-x-hidden z-50 shrink-0">
            {sidebarContent}
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {pg.sidebarOpen && (
          <>
            <motion.div key="backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => pg.setSidebarOpen(false)}
              className="fixed inset-0 bg-black/60 z-40 md:hidden" />
            <motion.aside key="sidebar" initial={{ x: -320 }} animate={{ x: 0 }} exit={{ x: -320 }}
              transition={{ type: "tween", duration: 0.25 }}
              className="fixed left-0 top-0 w-80 h-full bg-surface-container border-r border-white/5 flex flex-col py-8 overflow-y-auto z-50 md:hidden">
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-surface">

        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-white/5 z-40"
          style={{ background: "rgba(24,21,56,.8)", backdropFilter: "blur(16px)" }}>
          <div className="flex items-center gap-3">
            <button onClick={() => pg.setDesktopSidebar((v) => !v)}
              className="hidden md:flex w-8 h-8 items-center justify-center rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-white/10 transition-colors">
              <span className="material-symbols-outlined" style={{ fontSize: "20px" }}>menu</span>
            </button>
            <button onClick={() => pg.setSidebarOpen(true)} className="md:hidden">
              <span className="material-symbols-outlined text-on-surface">menu</span>
            </button>

            {pg.activeView === "chat" && pg.selectedTopic ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { pg.setActiveView("curriculum"); pg.setSelectedTopic(null); }}
                  className="flex items-center gap-1 text-on-surface-variant hover:text-on-surface text-xs transition-colors">
                  <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>arrow_back</span>
                  Müfredat
                </button>
                <span className="text-on-surface-variant text-xs">/</span>
                <span className="text-on-surface text-xs font-semibold">{pg.selectedTopic.name}</span>
                <span className="px-2 py-0.5 rounded-full text-xs font-bold"
                  style={{
                    background: LEVEL_META[pg.selectedTopic.level].bg,
                    color: LEVEL_META[pg.selectedTopic.level].color,
                  }}>
                  {LEVEL_META[pg.selectedTopic.level].label}
                </span>

                {/* Seviye hakimiyet progress */}
                <div className="flex items-center gap-1.5 ml-1">
                  <div className="w-20 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(151,169,255,.12)" }}>
                    <motion.div
                      className="h-full rounded-full"
                      animate={{ width: `${pg.levelProgress}%` }}
                      transition={{ duration: 0.4, ease: "easeOut" }}
                      style={{
                        background: pg.levelProgress >= 80
                          ? "linear-gradient(90deg,#34d399,#10b981)"
                          : "linear-gradient(90deg,#667eea,#f093fb)",
                      }}
                    />
                  </div>
                  <span className="text-xs font-bold" style={{ color: "rgba(151,169,255,.7)", minWidth: "28px" }}>
                    %{pg.levelProgress}
                  </span>
                </div>

                <button
                  onClick={() => pg.startChat(pg.selectedTopic!.id, pg.selectedTopic!.name, pg.selectedTopic!.level, true)}
                  className="flex items-center gap-1 text-xs text-on-surface-variant hover:text-primary transition-colors px-2 py-1 rounded-lg ml-1"
                  style={{ background: "rgba(255,255,255,.05)" }}
                  title="Geçmişi temizle ve yeni sohbet başlat">
                  <span className="material-symbols-outlined" style={{ fontSize: "15px" }}>add_comment</span>
                  Yeni Sohbet
                </button>
              </div>
            ) : (
              <span className="text-sm font-semibold text-on-surface hidden md:block">Müfredat</span>
            )}
          </div>

          <div className="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center gradient-bg md:hidden">
            {avatarUrl
              ? <img src={avatarUrl} alt={pg.name ?? ""} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              : <span className="text-white text-sm font-bold">{initials}</span>}
          </div>
        </header>

        {/* Views */}
        {pg.activeView === "curriculum" && (
          <CurriculumGrid
            masteredTopics={pg.masteredTopics}
            studiedTopics={pg.studiedTopics}
            lockedTopics={pg.lockedTopics}
            username={pg.username ?? undefined}
            onTopicClick={pg.openPreTest}
          />
        )}

        {pg.activeView === "chat" && (
          <ChatView
            messages={pg.messages}
            input={pg.input}
            streaming={pg.streaming}
            selectedTopic={pg.selectedTopic}
            onInputChange={pg.setInput}
            onSend={pg.sendMessage}
            onFeedback={async (_topicId, correct) => pg.handleFeedback(correct)}
            onPromptClick={pg.setInput}
          />
        )}
      </main>

      {/* Modals */}
      <PreTestModal
        preTest={pg.preTest}
        onClose={() => pg.setPreTest(null)}
        onAnswer={(step, opt) => pg.setPreTest((p) => p ? { ...p, answers: { ...p.answers, [step]: opt } } : p)}
        onNext={() => pg.setPreTest((p) => p ? { ...p, step: p.step + 1 } : p)}
        onSubmit={pg.submitPreTest}
        onStartChat={pg.startChat}
      />

      <QuizModal
        quizModal={pg.quizModal}
        pendingTestSuggest={pg.pendingTestSuggest}
        activeView={pg.activeView}
        onQuizAnswer={(step, opt) => pg.setQuizModal((p) => p ? { ...p, answers: { ...p.answers, [step]: opt } } : p)}
        onQuizNext={() => pg.setQuizModal((p) => p ? { ...p, step: p.step + 1 } : p)}
        onQuizDone={(score, total) => pg.setQuizModal((p) => p ? { ...p, done: true, score, total } : p)}
        onQuizClose={() => pg.handleQuizClose(pg.quizModal, pg.levelProgress)}
        onPendingAccept={async (topicId, topicName) => {
          pg.setPendingTestSuggest(null);
          const data = await getQuiz(topicId);
          if (data.questions?.length) {
            pg.setQuizModal({
              topicId, topicName, questions: data.questions,
              answers: {}, step: 0, done: false, mode: "review",
            });
          }
        }}
        onPendingDismiss={() => pg.setPendingTestSuggest(null)}
      />
    </div>
  );
}
