import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ChatBot from './pages/chatbot/ChatBot';
import Library from './pages/library/Library';
import LibraryDetail from './pages/library/LibraryDetail';
import CommonAlert from './comps/alert';
import { useAuth } from 'react-oidc-context';
import { Box, Button, Spinner } from '@cloudscape-design/components';
import ReSignIn from './comps/ReSignIn';
import { useTranslation } from 'react-i18next';
import SessionHistory from './pages/history/SessionHistory';
import SessionDetail from './pages/history/SessionDetail';
import PromptList from './pages/prompts/PromptList';
import ChatbotManagement from './pages/chatbotManagement/ChatbotManagement';

// import LoginCallback from './comps/LoginCallback';
import Intention from './pages/intention/Intention';
import IntentionDetail from './pages/intention/IntentionDetail';
import Home from './pages/home/Home';
import ChatbotDetail from './pages/chatbotManagement/ChatbotDetail';
import CustomerService from './pages/customService/CustomerService';
import { ROUTES } from './utils/const';
import Login from './pages/login';
import FindPWD from './pages/find-pwd';
import Register from './pages/register';
import ChangePWD from './pages/change-pwd';

const SignedInRouter = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path={ROUTES.Login} element={<Login />} />
        <Route path={ROUTES.FindPWD} element={<FindPWD />} />
        <Route path={ROUTES.Register} element={<Register />} />
        <Route path={ROUTES.ChangePWD} element={<ChangePWD />} />
        <Route path={ROUTES.Home} element={<Home />} />
        <Route path={ROUTES.Chat} element={<ChatBot />} />
        <Route path={ROUTES.Library} element={<Library />} />
        <Route path={ROUTES.LibraryDetail} element={<LibraryDetail />} />
        <Route path={ROUTES.Session} element={<SessionHistory />} />
        <Route path={ROUTES.SessionDetail} element={<SessionDetail />} />
        <Route path={ROUTES.Prompt} element={<PromptList />} />
        <Route path={ROUTES.Intention} element={<Intention />} />
        <Route path={ROUTES.IntentionDetail} element={<IntentionDetail />} />
        <Route path={ROUTES.Chatbot} element={<ChatbotManagement />} />
        <Route path={ROUTES.ChatbotDetail} element={<ChatbotDetail />} />
        <Route path={ROUTES.Workspace} element={<CustomerService />} />
        <Route path={ROUTES.WorkspaceChat} element={<CustomerService />} />
      </Routes>
      <CommonAlert />
    </BrowserRouter>
  );
};

const AppRouter = () => {
  const auth = useAuth();
  const { t } = useTranslation();
  if (auth?.isLoading) {
    return (
      <div className="page-loading">
        <Spinner />
      </div>
    );
  }

  if (auth?.error) {
    return (
      <>
        <ReSignIn />
        <SignedInRouter />
      </>
    );
  }

  // auth.isAuthenticated = true
  if (auth?.isAuthenticated) {
  return <SignedInRouter />;
  }
  return (
    <SignedInRouter />
    // <>
    // <div className="login-container">
    //   <div className="text-center">
    //     <Box variant="h2">{t('welcome')}</Box>
    //     <div className="mt-10">
    //       <Button variant="primary" onClick={() => void auth.signinRedirect()}>
    //         {t('button.login')}
    //       </Button>
    //     </div>
    //   </div>
    // </div>
    // </>
  );
};

export default AppRouter;
