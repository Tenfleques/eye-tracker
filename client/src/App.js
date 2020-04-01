import React, { Component } from 'react';
import { HashRouter, Route } from 'react-router-dom';
// import PrivateRoute from "./Components/privateRoute"

import Home from "./Pages/Home";

import DataCapture from "./Pages/DataCapture";

import NavBar from "./Components/Navbar";

import PrivateNavs from "./Routes/private"
import PublicNavs from "./Routes/public"

import './Css/bootstrap.css';
import './Css/App.css';

class App extends Component {
  render() {
    return (
      <HashRouter basename="">
          {(sessionStorage.getItem('user') 
            && <NavBar navs={PrivateNavs} className="mb-5" /> )
          || <NavBar navs={PublicNavs} className="mb-5" />}
          {/* <Route exact strict path="/login" component={Login} /> */}
          <Route exact path="/" component={Home} />
          {/* <PrivateRoute exact strict  path="/" component={Home} /> */}
          {/* <PrivateRoute exact strict path="/data_capture" component={DataCapture} /> */}

          <Route 
            exact strict path="/data_capture" 
            render={(props) => <DataCapture 
              {...props}
            />} 
          />
      </HashRouter>
    );
  }
}

export default App;
