import { Divider, Paper, Typography } from "@mui/material";
import React, { Component, Fragment } from "react";
import { makeStyles } from '@mui/styles';

const useStyles = makeStyles({
  LogoFooter: {
    paddingTop: '3em',
    margiBottom: '2em'
  }

});


export default function Logo() {

  const classes = useStyles();
    return (
      
      <Fragment>
      <Divider></Divider>
        <footer style={{ display: "block", marginLeft: "auto", marginRight: "auto", width: "20%" }}>
          <a
            href="https://www.tmforum.org"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Typography>Powered by { }</Typography>
            <Logo className={classes.LogoFooter}></Logo>
            
          </a>
        </footer>
        </Fragment>

    )
}
