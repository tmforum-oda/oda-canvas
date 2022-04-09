import { Divider, Paper, Typography } from "@mui/material";
import React, { Component, Fragment } from "react";
import { makeStyles } from '@mui/styles';
import Logo from "./Logo"

const useStyles = makeStyles({
  LogoFooter: {
    paddingTop: '4em',
    marginBottom: '2em'
  },
  poweredByFooter: {
    float: "left",
    paddingTop: '0.25em'
  },
  footerDivider: {
    marginBottom: "0.5em"
  }

});


export default function Footer() {

  const classes = useStyles();
    return (
      
      <Fragment>
      <Divider className={classes.footerDivider}></Divider>
        <footer style={{ display: "block", marginLeft: "auto", marginRight: "auto", width: "20%" }}>
        
          <a
            href="https://www.tmforum.org"
            target="_blank"
          >
            <Typography variant='h6' className={classes.poweredByFooter}>Powered by:</Typography>
            <Logo className={classes.LogoFooter}></Logo>
            
          </a>
        </footer>
        </Fragment>

    )
}
