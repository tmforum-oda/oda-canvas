import React, { Component, Fragment } from "react";

class Footer extends Component {
    render() {
        return (
            <footer style={{display: "block", marginLeft: "auto", marginRight: "auto", width: "20%"}}>
            <a
              href="https://www.tmforum.org"
              target="_blank"
            >
              Powered by{' '}
              <img src="/TMForum_logo_2021.svg" alt="TM Forum" className="logo" />
            </a>
          </footer>

        )
    }
}

export default Footer;