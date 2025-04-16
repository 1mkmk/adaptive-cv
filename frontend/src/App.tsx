import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Header from './components/layout/header';
import Footer from './components/layout/footer';
import Sidebar from './components/layout/sidebar';
import Index from './pages/index';
import Editor from './pages/editor';
import Templates from './pages/templates';
import Preview from './pages/preview';

const App: React.FC = () => {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <Sidebar />
        <main>
          <Switch>
            <Route path="/" exact component={Index} />
            <Route path="/editor" component={Editor} />
            <Route path="/templates" component={Templates} />
            <Route path="/preview" component={Preview} />
          </Switch>
        </main>
        <Footer />
      </div>
    </Router>
  );
};

export default App;