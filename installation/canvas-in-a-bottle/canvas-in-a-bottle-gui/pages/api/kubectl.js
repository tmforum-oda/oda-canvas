const { exec } = require('child_process');

export default function handler(req, res) {
    if (req.method === 'POST') {
        exec("kubectl get all --all-namespaces", (error, stdout, stderr) => {
            if (error) {
                console.error(`exec error: ${error}`);
                return;
            }

            res.status(200).json({"data": stdout})
        });
    } else {
        res.status(200).json({})
    }

}