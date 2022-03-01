const { execSync, spawn, spawnSync } = require('child_process');

export default function handler(req, res) {
    const options = {
        slient:true,
        detached:true,
          stdio: [null, null, null, 'ipc']
      };
    var logs = ''
    if (req.method === 'GET') {


        try {
            logs += spawn("kubectl", ["proxy"], options)
        }

        catch (error) {
            console.error(`execSync error: ${error}`);
            res.status(500).json({ "data": null, "error": JSON.stringify(error), "logs": logs })
            return;
        }
        res.status(200).json({ "data": "", "logs": "Proxy started sucessfully on Port 8001", "error": null })
    }
    else {
        res.status(501).json({})
    }
}