const express = require('express')
const fs = require('fs')
const path = require('path')

const config = require('../config')
const logger = require('../logger');

const args = process.env

const app = express()

const FILEDIR = args.FILEDIR || '/opt/app/files'
const UPLOADDIR = args.FILEDIR  || '/tmp/uploads/'
const PORT = args.FILESERVER_PORT || config.FILESERVER_PORT

if (!fs.existsSync(FILEDIR)) {
    fs.mkdirSync(FILEDIR, { recursive: true })
} 

if (!fs.existsSync(UPLOADDIR)) {
  fs.mkdirSync(UPLOADDIR, { recursive: true })
} 

app.get('/fileserver/:file', (req, res, next) => {
  try {
    const filename = req.params.file

    if(filename.startsWith('.')) {
      res.sendStatus(404)
      return
    }

    logger.info('get:: ' + filename + ' headers: ' + JSON.stringify(req.headers))

    res.sendFile(FILEDIR + '/' + filename, function (err) {
      if (err) {
        res.sendStatus(404)
      } else {
        logger.info('/fileserver:: sent: ', filename)
      }
    })
  
  } catch(error) {
    logger.info('/fileserver:: error=', error)
  }

})

app.post('/fileserver/:filename', function (req, res, next) {
  const filename = req.params.filename

  logger.info('post:: ' + filename + ' headers: ' + JSON.stringify(req.headers))

  if(!isFileAllowed(filename)) {
    logger.info('post:: not allowed filename: ' + filename)

    res.sendStatus(500)
    return
  }

  const tmpFile = path.join(UPLOADDIR, filename)
  const destFile = path.join(FILEDIR, filename)

  const output = fs.createWriteStream( tmpFile )
  
  req.pipe(output)
  
  output.on('finish', () => {
    logger.debug('post:: finish')
    output.close()
    fs.copyFile(tmpFile, destFile, (err) => {
      if ( err ) {
        logger.info('post:: finish ERROR: ' + err)
        res.sendStatus(500)
        fs.unlinkSync(tmpFile)
      } else {
        logger.info("post:: OK filename=" + filename)
        res.sendStatus(200)
        fs.unlinkSync(tmpFile)
      }
    })
  })

})

app.listen(PORT, function () {
  logger.info('File server started at port ' + PORT + ' FILEDIR=' + FILEDIR)
})

function isFileAllowed(filename) {
  return !filename.startsWith('.')
}
