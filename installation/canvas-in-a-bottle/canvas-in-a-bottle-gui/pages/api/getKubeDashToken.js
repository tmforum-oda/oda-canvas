const { execSync, spawn, spawnSync } = require('child_process');
const fs = require('fs');
const yaml = require('js-yaml')

export default function handler(req, res) {
    var token;
    if (req.method === 'GET') {
        let tokenFull = execSync("/root/get_dashboard_token").toString()
        
        token = tokenFull.split("token:      ")[1].replace('\n','')
        res.status(200).send(token)
    }
}