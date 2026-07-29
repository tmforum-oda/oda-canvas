'use strict';

const {TError, TErrorEnum} = require('../utils/errorUtils');

const logger = require('../logger');

const { getRequestServiceType, getTypeDefinition } = require('./swaggerUtils');


function processAssignmentRules(operation, doc) {

  logger.debug("processAssignmentRules: operation=" + operation)

  return new Promise(function(resolve, reject) {

    //
    // TMF620_Product_Catalog
    //

    if (operation === 'tMF620createCatalog'){
      //doc.lifecycleStatus= "Active"
    }
    
    //
    // TMF641B_Service_Ordering_Conformance_Profile_R18.0.0.docx
    //
    if (operation === 'tMF641serviceOrderCreate'){
      doc.state = 'acknowledged';
      doc.startDate = new Date()
      doc.orderDate = new Date()
      doc.orderItem.forEach(item => item.state = 'acknowledged' )
    } 

    //
    // TMF645B_Service_Qualification_Conformance_Profile_R18.0.0.docx
    //
    if (operation === 'tMF645serviceQualificationCreate'){
      doc.state = 'acknowledged';
      doc.serviceQualificationDate = new Date()

      doc.serviceQualificationItem.forEach(item => item.state = 'acknowledged')
    } 

    //
    // TMF646B_Appointment_API_Conformance_Profile_R18.0.0.docx
    //
    if (operation === 'tMF646appointmentCreate'){
      doc.status = 'initialized';
      doc.creationDate = new Date()
    } 

    //
    // TMF648B_Quote_Management_Conformance_Profile_R17.5.0.docx
    //
    if (operation === 'tMF648quoteCreate '){
      doc.state = 'inProgress';
      doc.quoteDate = new Date()
      doc.quoteItem.forEach(item => item.state = 'inProgress' ); 

      if(doc.note && !doc.note.date) doc.note.date = new Date() // TODO: Check

    }

    //
    //  TMF666-AccountManagement
    //
    if (operation === 'tMF666createPartyAccount'){
      doc.state = 'acknowledged';
    }
    
    //
    // CTK-TMF679-ProductOfferingQualification-R18.0
    //
    if (operation === 'tMF679productOfferingQualificationCreate'){
      doc.productOfferingQualificationDateTime = new Date()
      doc.state = 'acknowledged';
      doc.productOfferingQualificationItem.forEach(item => item.state = 'acknowledged' );
      doc.productOfferingQualificationItem.forEach(item => item.qualificationItemResult = 'qualified' )
    }

    if (operation === "createReserveProductStock"){
      doc.reserveProductStockState = "accepted"
      doc.reserveProductStockItem.forEach(item => item.reserveProductStockState = "accepted")
    }

    if(operation === 'createQueryProductRecommendation') {
      doc.recommendationItem = [
        {
            "id": "1",
            "priority": 1,
            "product": {
                "productOffering": {
                    "id": "6547",
                    "href": "https://host:port/productOffering/v1/productOffering/6547",
                    "name": "TMFone "
                },
                "productCharacteristic": [
                    {
                        "name": "capacity",
                        "valueType": "string",
                        "value": { "value": "128 Gb" }
                    }
                ]
            }
        },
        {
            "id": "2",
            "priority": 2,
            "product": {
                "productOffering": {
                    "id": "6542",
                    "href": "https://host:port/productOffering/v1/productOffering/6542",
                    "name": " TMFone Case"
                },
                "productCharacteristic": [
                    {
                        "name": "material",
                        "valueType": "string",
                        "value": { "value": "plastic" } 
                    },
                    {
                        "name": "material",
                        "valueType": "string",
                        "value": { "value": "leather" } 
                    }
                ]
            }
        }
      ]
    }

    resolve(doc)

  })
}


function processAssignmentRulesByType(req, type, doc) {
  return new Promise(function(resolve, reject) {

    // NaaS specifics
    if(type!==undefined && type==='ResponseHub') {
      // - "createdTime"
      // - "id"
      // - "serviceType"

      var typedef = getTypeDefinition(type);

      if(typedef.properties!==undefined) {
        typedef = typedef.properties
      }
      
      if(typedef.createdTime!==undefined && doc.createdTime===undefined) {
        doc.createdTime = new Date()
      }

      if(typedef.id!==undefined && doc.id==undefined) {
        doc.id = uuid.v4()
      }

      if(typedef.serviceType!==undefined && doc.serviceType==undefined) {
        const res = getRequestServiceType(req);
        if(res!==undefined) {
          doc.serviceType = res.value
        }
      }
    }
    resolve(doc)
  })
}

module.exports = { processAssignmentRules, processAssignmentRulesByType }

