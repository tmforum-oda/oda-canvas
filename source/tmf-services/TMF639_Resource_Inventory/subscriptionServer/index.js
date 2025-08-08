'use strict'

const logger = require('../logger')

const plugins = require('../plugins/plugins')

const config = require('../config')
const axios = require('axios')

const nodemailer = require("nodemailer");

const processEvent = (event,done) => {
  try {    
    logger.info("subscriptionServer:: event=" + JSON.stringify(event,null,2))
 
    const uri=event.uri
    if(uri.startsWith('http')) {
      axios.post(event.uri, event.body)
          .then((response) => {
            logger.info("subscriptionServer::response=" + response)
          })
          .catch((error) => {
            logger.info("subscriptionServer::error=" + error)
          })
    } else if(uri.startsWith('mail')) {
      const recipient=uri.split(':')[1]
      const content = JSON.stringify(event.body,null,2)
      const subject = event.body.eventType
      sendmail(recipient,subject,content)
    }

  } catch(e) {
    logger.info("subscriptionServer::error=" + e)
  }
}

async function sendmail(recipient, subject, content) {

  const smtpEndpoint = config.SMTP_HOST
  const port = config.SMTP_PORT

  const senderAddress = config.SMTP_SENDER_ADDRESS

  const smtpUsername = config.SMTP_USER_NAME 
  const smtpPassword = config.SMTP_PASSWORD

  const transporter = nodemailer.createTransport({
      host: smtpEndpoint,
      port: port,
      secure: false, // true for 465, false for other ports
      auth: {
        user: smtpUsername,
        pass: smtpPassword
      }
  })

  let mailOptions = {
      from: senderAddress,
      to: recipient,
      subject: subject,
      text: content,
      html: '',
      headers: {
      }
    }

  logger.info(`subscriptionServer:: mail:: recipient=${recipient} subject=${subject}`)

  let info = await transporter.sendMail(mailOptions)
  
  logger.info(`subscriptionServer:: mail: sent messageId=${info.messageId}` )

}

plugins.waitForPlugins()
.then( () => {

  logger.info("subscriptionServer::plugins ok")

  plugins.queue.setConsumer('subscriptionServer')
  plugins.queue.consume(config.SUBSCRIPTION || "subscription", processEvent)

})
.catch( error => {
  logger.error(`subscriptionServer:: unable to connect to all plugins: error=${error}`)
})

