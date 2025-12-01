'use strict';

const validationRules = {
  
  tMF645serviceQualificationCreate: 
    [{ $: [{$noneOf: ["id", "href", "serviceQualificationDate", "state", "qualificationResult", 
                        "estimatedResponseDate", "effectiveQualificationDate", 
                        "eligibilityUnavailabilityReason", "alternateServiceProposal",
                        "expirationDate"]},
           {$present: ['serviceQualificationItem']}]},
     {"serviceQualificationItem": {$present: ["id"]}},
     {"serviceQualificationItem": {$noneOf: ["expirationDate", "qualificationItemResult"]}},
     {"serviceQualificationItem.qualificationItemRelationship": {$present: ["id", "type"]}},
     {"serviceQualificationItem.relatedParty": {$eitherOf: ["href", "id"]}},
     {"serviceQualificationItem.service.serviceCharacteristic": {$present: ["name", "value"]}}],

  //
  // TMF 641 Service Order, based on TMF641B Release 18.0.1 May 2018
  //   
  // Notes: 
  // 1) Handling of 'state' in POST is unclear in the document, here treated as not allowed
  // 2) orderItem is incorrectly labelled as 'serviceOrderItem' in TMF641B
  // 3) removed rule { "orderItem.action": {$notEqual: "add", $eitherOf: ["service.id", "service.href"]}}
  // 
  tMF641serviceOrderCreate:
    [{ $: { $noneOf: ["id", "href", "state", "orderDate", "completionDate", 
                        "expectedCompletionDate", "startDate"]}},
    { $: {$eitherOf: ["orderItem"]}},
    { "relatedParty": {$eitherOf: ["id", "href"]}},
    { "note": {$eitherOf: ["author", "text"]}},
    { "orderItem": {$notEmpty: true}},
    { "orderItem": {$present: ["action","id"]}},
    { "orderItem": {$noneOf: ["state"]}},
    { "orderItem.appointment": {$eitherOf: ["id", "href"]}},
    { "orderItem.orderItemRelationship": {$present: ["type", "id"]}},
    { "orderItem.service": {$eitherOf: ["id", "href"]}},
    { "orderItem.service": {$eitherOf: ["id", "href"]}},
    { "orderItem.service.serviceSpecification": {$eitherOf: ["id", "href"]}},  
	  { "orderItem.service.serviceSpecification.targetServiceSchema": {$present: ["@type", "@schemaLocation"]}},  
    { "orderItem.service.serviceRelationship": {$eitherOf: ["type", "service"] }},
    { "orderItem.service.serviceCharacteristic": {$eitherOf: ["name", "valueType", "value"]}},
    { "orderItem.service.place": {$eitherOf: ["id", "href"]}},
    { "orderItem.service.place": {$present: ["role", "@referredType"]}},
    { "orderItem.relatedParty": {$present: ["type"]}},
    { "orderItem.relatedParty": {$eitherOf: ["id", "href"]}},
    { "orderItem.orderRelationship": {$present: ["type"]}},
    { "orderItem.orderRelationship": {$eitherOf: ["id", "href"]}}
  ]


};

const validationRulesType2 = {
  "Customer": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {"engagedParty": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"contactMedium": {$present: ["type", "characteristic"]}},
      {"account": {$present: ["name"]}},
      {"account": {$eitherOf: ["id", "href"]}},
      {"creditProfile": {$present: ["creditProfileDate", "validFor"]}},
      {"paymentMethod": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"engagedParty": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"contactMedium": {$present: ["type", "characteristic"]}},
      {"account": {$present: ["name"]}},
      {"account": {$eitherOf: ["id", "href"]}},
      {"creditProfile": {$present: ["creditProfileDate", "validFor"]}},
      {"paymentMethod": {$eitherOf: ["id", "href"]}}
    ],
  },

  "BalanceReserve": {
    "operations": ["POST"],
    "POST": [
      {$: {$present: ["id", "relatedParty", "reservedAmount"]}}
    ],
  },

  "RoleType": {
  },

  "Product": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"productOffering": {$eitherOf: ["id", "href"]}},
      {"productSpecification": {$eitherOf: ["id", "href"]}},
      {"billingAccount": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["name", "relatedParty"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "orderDate"]}},
      {"productOffering": {$eitherOf: ["id", "href"]}},
      {"productSpecification": {$eitherOf: ["id", "href"]}},
      {"billingAccount": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}}
    ],
  },

  "SLA": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      
    ],
  },

  "Extract": {
    "operations": ["POST"],
    "POST": [
      
    ],
    "PATCH": [
      
    ],
  },

  "ResourcePool": {
    "operations": ["POST", "PATCH", "DELETE"],
    "POST": [
      
    ],
    "PATCH": [
      
    ],
  },

  "ChangeRequest": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"sla": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"specification": {$eitherOf: ["id", "href"]}},
      {"impactEntity": {$eitherOf: ["id", "href"]}},
      {"relatedChangeRequest": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"resolution": {$present: ["name", "description"]}},
      {"targetEntity": {$eitherOf: ["id", "href"]}},
      {"workLog": {$present: ["createDateTime", "record"]}},
      {$: {$present: ["status"]}},
      {$: {$present: ["priority"]}},
      {$: {$present: ["targetEntity"]}},
      {$: {$present: ["specification"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"sla": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"specification": {$eitherOf: ["id", "href"]}},
      {"impactEntity": {$eitherOf: ["id", "href"]}},
      {"relatedChangeRequest": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"resolution": {$present: ["name", "description"]}},
      {"targetEntity": {$eitherOf: ["id", "href"]}},
      {"workLog": {$present: ["createDateTime", "record"]}}
    ],
  },

  "Document": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"partyRoleRef": {$eitherOf: ["id", "href"]}},
      {"documentCharacteristic": {$present: ["name", "value"]}},
      {"attachment": {$present: ["size"]}},
      {$: {$present: ["attachment.sizeUnit"]}},
      {"attachment": {$present: ["mimeType"]}},
      {"categoryRef": {$eitherOf: ["id", "href"]}},
      {"relatedObject": {$present: ["involvement", "reference"]}},
      {$: {$present: ["description"]}},
      {$: {$present: ["type"]}},
      {$: {$present: ["attachment"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "created"]}},
      {"partyRoleRef": {$eitherOf: ["id", "href"]}},
      {"documentCharacteristic": {$present: ["name", "value"]}},
      {"attachment": {$present: ["size"]}},
      {$: {$present: ["attachment.sizeUnit"]}},
      {"attachment": {$present: ["mimeType"]}},
      {"categoryRef": {$eitherOf: ["id", "href"]}},
      {"relatedObject": {$present: ["involvement", "reference"]}}
    ],
  },

  "BalanceDeductRollback": {
    "operations": ["POST"],
    "POST": [
      {$: {$present: ["id", "relatedParty", "balanceDeduct"]}}
    ],
  },

  "Reservation": {
    "operations": ["GET", "POST", "PATCH"],
    "POST": [
      {$: {$present: ["relatedParty", "resourceCapacityDemand"]}}
    ],
    "PATCH": [
      
    ],
  },

  "CommunicationMessage": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"receiver": {$present: ["id"]}},
      {"sender": {$present: ["id"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"attachment": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["type", "content", "sender", "receiver"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "name"]}},
      {"receiver": {$present: ["id"]}},
      {"sender": {$present: ["id"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"attachment": {$eitherOf: ["id", "href"]}}
    ],
  },

  "ServiceLevelSpecification": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"objective": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["name"]}},
      {$: {$present: ["objective"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "validFor"]}},
      {"objective": {$eitherOf: ["id", "href"]}}
    ],
  },

  "ServiceProblem": {
    "operations": ["GET", "PATCH", "POST"],
    "POST": [
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["category", "priority", "description", "reason", "originatorParty"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "correlationId", "originatingSystem", "href", "firstAlert", "timeRaised", "trackingRecord", ""]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}}
    ],
  },

  "SettlementAccount": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name", "relatedParty"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "accountBalance"]}},
    ],
  },

  "Street": {
    "operations": ["GET"],
  },

  "BillFormat": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "LogicalResource": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"resourceSpecification": {$eitherOf: ["id", "href"]}},
      {"partyRole": {$eitherOf: ["id", "href"]}},
      {"resourceRelationship": {$present: ["type"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}},
      {"place": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["value"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"resourceSpecification": {$eitherOf: ["id", "href"]}},
      {"partyRole": {$eitherOf: ["id", "href"]}},
      {"resourceRelationship": {$present: ["type"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}},
      {"place": {$eitherOf: ["id", "href"]}}
    ],
  },

  "Push": {
    "operations": ["POST"],
    "POST": [
      
    ],
    "PATCH": [
      
    ],
  },

  "BalanceDeduct": {
    "operations": ["POST"],
    "POST": [
      {$: {$present: ["id", "relatedParty", "balanceReserve"]}}
    ],
  },

  "StreetSegment": {
    "operations": ["GET"],
  },

  "PartyRole": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {"engagedParty": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"contactMedium": {$present: ["type", "characteristic"]}},
      {"account": {$present: ["name"]}},
      {"account": {$eitherOf: ["id", "href"]}},
      {"creditProfile": {$present: ["creditProfileDate", "validFor"]}},
      {"paymentMethod": {$eitherOf: ["id", "href"]}},
      {"type": {$present: ["name"]}},
      {$: {$present: ["name", "type"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"engagedParty": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"contactMedium": {$present: ["type", "characteristic"]}},
      {"account": {$present: ["name"]}},
      {"account": {$eitherOf: ["id", "href"]}},
      {"creditProfile": {$present: ["creditProfileDate", "validFor"]}},
      {"paymentMethod": {$eitherOf: ["id", "href"]}},
      {"type": {$present: ["name"]}}
    ],
  },

  "GeographicLocation": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
  },

  "Resource": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"resourceSpecification": {$eitherOf: ["id", "href"]}},
      {"partyRole": {$eitherOf: ["id", "href"]}},
      {"resourceRelationship": {$present: ["type"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}},
      {"place": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["name", "@type"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"resourceSpecification": {$eitherOf: ["id", "href"]}},
      {"partyRole": {$eitherOf: ["id", "href"]}},
      {"resourceRelationship": {$present: ["type"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}},
      {"place": {$eitherOf: ["id", "href"]}}
    ],
  },

  "ServiceTestSpecification": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"relatedServiceSpecification": {$eitherOf: ["id", "href"]}},
      {"validFor": {$present: ["endDateTime", "startDateTime"]}},
      {"testMeasureDefinition": {$present: ["metricName", "metricHref", "name"]}},
      {"testMeasureDefinition.capturePeriod": {$present: ["endDateTime", "startDateTime"]}},
      {"testMeasureDefinition.thresholdRule": {$present: ["conformanceTargetLower", "conformanceTargetUpper", "conformanceComparatorLower", "conformanceComparatorUpper", "name"]}},
      {$: {$present: ["name"]}},
      {$: {$present: ["relatedServiceSpecification"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "validFor"]}},
      {"relatedServiceSpecification": {$eitherOf: ["id", "href"]}},
      {"validFor": {$present: ["endDateTime", "startDateTime"]}},
      {"testMeasureDefinition": {$present: ["metricName", "metricHref", "name"]}},
      {"testMeasureDefinition.capturePeriod": {$present: ["endDateTime", "startDateTime"]}},
      {"testMeasureDefinition.thresholdRule": {$present: ["conformanceTargetLower", "conformanceTargetUpper", "conformanceComparatorLower", "conformanceComparatorUpper", "name"]}}
    ],
  },

  "Catalog": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "Recommendation": {
    "operations": ["GET"],
  },

  "Area": {
    "operations": ["GET"],
  },

  "AssociationSpecification": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name", "associationRoleSpec"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "BalanceUnreserve": {
    "operations": ["POST"],
    "POST": [
      {$: {$present: ["id", "relatedParty", "balanceReserve"]}}
    ],
  },

  "FinancialAccount": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {"taxExemption": {$present: ["issuingJurisdiction", "validFor"]}},
      {"accountRelationship": {$present: ["relationshipType", "validFor"]}},
      {"contact": {$present: ["contactType", "validFor"]}},
      {"relatedParty": {$present: ["id", "name"]}},
      {"accountBalance": {$present: ["type", "amount", "validFor"]}},
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {"taxExemption": {$present: ["issuingJurisdiction", "validFor"]}},
      {"accountRelationship": {$present: ["relationshipType", "validFor"]}},
      {"contact": {$present: ["contactType", "validFor"]}},
      {"relatedParty": {$present: ["id", "name"]}},
      {"accountBalance": {$present: ["type", "amount", "validFor"]}}
    ],
  },

  "Individual": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"disability": {$present: ["disability"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"identification": {$present: ["type", "identificationId"]}},
      {"externalReference": {$present: ["type", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {$: {$present: ["givenName", "familyName"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"disability": {$present: ["disability"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"identification": {$present: ["type", "identificationId"]}},
      {"externalReference": {$present: ["type", "href"]}},
      {"relatedParty": {$present: ["role"]}}
    ],
  },

  "EntityCatalog": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "GeographicAddressValidation": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "ImportJob": {
    "operations": ["GET", "POST"],
    "POST": [
      
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      
    ],
  },

  "AgreementSpecification": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name", "attachment"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "ServiceTest": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"relatedService": {$eitherOf: ["id", "href"]}},
      {"testSpecification": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"testMeasure.ruleViolation": {$present: ["name", "conformanceTargetLower", "conformanceTargetUpper", "conformanceComparatorLower", "conformanceComparatorUpper"]}},
      {"testMeasure": {$present: ["metricHref", "metricName"]}},
      {$: {$present: ["name"]}},
      {$: {$present: ["relatedService"]}},
      {$: {$present: ["testSpecification"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"relatedService": {$eitherOf: ["id", "href"]}},
      {"testSpecification": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"testMeasure.ruleViolation": {$present: ["name", "conformanceTargetLower", "conformanceTargetUpper", "conformanceComparatorLower", "conformanceComparatorUpper"]}},
      {"testMeasure": {$present: ["metricHref", "metricName"]}}
    ],
  },

  "Organization": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"identification": {$present: ["type", "identificationId"]}},
      {"externalReference": {$present: ["type", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {$: {$present: ["tradingName"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"characteristic": {$present: ["name", "value"]}},
      {"identification": {$present: ["type", "identificationId"]}},
      {"externalReference": {$present: ["type", "href"]}},
      {"relatedParty": {$present: ["role"]}}
    ],
  },

  "BillPresentationMedia": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "EntityCatalogItem": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "BillingCycleSpecification": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "CustomerBill": {
    "operations": ["GET", "PATCH"],
    "PATCH": [
    ],
  },

  "GeographicSite": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["name", "id", "type"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}}
    ],
  },

  "PhysicalResource": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"resourceSpecification": {$eitherOf: ["id", "href"]}},
      {"partyRole": {$eitherOf: ["id", "href"]}},
      {"resourceRelationship": {$present: ["type"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}},
      {"place": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["name", "serialNumber"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"resourceSpecification": {$eitherOf: ["id", "href"]}},
      {"partyRole": {$eitherOf: ["id", "href"]}},
      {"resourceRelationship": {$present: ["type"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}},
      {"place": {$eitherOf: ["id", "href"]}}
    ],
  },

  "Promotion": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"pattern": {$present: ["id", "name"]}},
      {"pattern.action": {$present: ["id", "actionType", "actionValue", "actionObjectId"]}},
      {"pattern.criteriaGroup.criteria": {$present: ["id", "criteriaPara", "criteriaOperator", "criteriaValue"]}},
      {"pattern.criteriaGroup": {$present: ["id", "groupName", "relationTypeInGroup"]}},
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {"pattern": {$present: ["id", "name"]}},
      {"pattern.action": {$present: ["id", "actionType", "actionValue", "actionObjectId"]}},
      {"pattern.criteriaGroup.criteria": {$present: ["id", "criteriaPara", "criteriaOperator", "criteriaValue"]}},
      {"pattern.criteriaGroup": {$present: ["id", "groupName", "relationTypeInGroup"]}}
    ],
  },

  "Party": {
  },

  "Association": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name", "associationRole"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "SLAViolation": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      
    ],
  },

  "GeographicAddress": {
    "operations": ["GET"],
  },

  "ExportJob": {
    "operations": ["GET", "POST"],
    "POST": [
      
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      
    ],
  },

  "BillingAccount": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name", "relatedParty"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "accountBalance"]}},
    ],
  },

  "UsageSpecification": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["nONE"]}},
      {$: {$present: ["nONE"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      {$: {$present: ["nONE"]}}
    ],
  },

  "PartyAccount": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["name", "relatedParty"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "accountBalance"]}},
    ],
  },

  "ProductOrder": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"orderItem": {$present: ["id", "action", "billingAccount", "product"]}},
      {"billingAccount": {$eitherOf: ["id", "href"]}},
      {"payment": {$eitherOf: ["id", "href"]}},
      {"note": {$present: ["text"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {"orderItem.qualification": {$eitherOf: ["id", "href"]}},
      {"orderItem.payment": {$eitherOf: ["id", "href"]}},
      {"orderItem.appointment": {$eitherOf: ["id", "href"]}},
      {"orderItem.product.place": {$present: ["role"]}},
      {"orderItem.productOffering": {$eitherOf: ["id", "href"]}},
      {"orderItem.itemTerm": {$present: ["name", "duration"]}},
      {"orderItem.orderItemRelationship": {$present: ["type", "id"]}},
      {"orderItem.action": {$equal: "modify", "orderItem.product": {$eitherOf: ["id", "href"]}}},
      {"orderItem.action": {$equal: "delete", "orderItem.product": {$eitherOf: ["id", "href"]}}},
      {$: {$present: ["relatedParty", "orderItem"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "externalId", "orderDate", "completionDate", "expectedCompletionDate", "state"]}},
      {"orderItem": {$present: ["id", "action", "billingAccount", "product"]}},
      {"billingAccount": {$eitherOf: ["id", "href"]}},
      {"payment": {$eitherOf: ["id", "href"]}},
      {"note": {$present: ["text"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {"orderItem.qualification": {$eitherOf: ["id", "href"]}},
      {"orderItem.payment": {$eitherOf: ["id", "href"]}},
      {"orderItem.appointment": {$eitherOf: ["id", "href"]}},
      {"orderItem.product.place": {$present: ["role"]}},
      {"orderItem.productOffering": {$eitherOf: ["id", "href"]}},
      {"orderItem.itemTerm": {$present: ["name", "duration"]}},
      {"orderItem.orderItemRelationship": {$present: ["type", "id"]}},
      {"orderItem.action": {$equal: "modify", "orderItem.product": {$eitherOf: ["id", "href"]}}},
      {"orderItem.action": {$equal: "delete", "orderItem.product": {$eitherOf: ["id", "href"]}}}
    ],
  },

  "ResourceOrder": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"note": {$present: ["text"]}},
      {"appointment": {$eitherOf: ["id", "href"]}},
      {"orderItem": {$present: ["id", "action", "resource"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"orderItem.resource.place": {$present: ["role"]}},
      {"orderItem.resourceCandidate": {$eitherOf: ["id", "href"]}},
      {"orderItem.action": {$equal: "add", $present: ["characteristic"]}},
      {"orderItem.action": {$equal: "modify", "orderItem.resource": {$eitherOf: ["id", "href"]}}},
      {"orderItem.action": {$equal: "delete", "orderItem.resource": {$eitherOf: ["id", "href"]}}},
      {$: {$present: ["orderItem"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "corelationId", "orderDate", "completionDate", "orderItem.id", "orderItem.action"]}},
      {"note": {$present: ["text"]}},
      {"appointment": {$eitherOf: ["id", "href"]}},
      {"orderItem": {$present: ["id", "action", "resource"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"orderItem.resource.place": {$present: ["role"]}},
      {"orderItem.resourceCandidate": {$eitherOf: ["id", "href"]}},
      {"orderItem.action": {$equal: "add", $present: ["characteristic"]}},
      {"orderItem.action": {$equal: "modify", "orderItem.resource": {$eitherOf: ["id", "href"]}}},
      {"orderItem.action": {$equal: "delete", "orderItem.resource": {$eitherOf: ["id", "href"]}}}
    ],
  },

  "Usage": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["date", "type"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
      
    ],
  },

  "PartnershipType": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {"roleType": {$present: ["name"]}},
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {"roleType": {$present: ["name"]}}
    ],
  },

  "ProductOfferingQualification": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"productOfferingQualificationItem": {$present: ["category", "productOffering", "product"]}},
      {"productOffering": {$eitherOf: ["id", "href"]}},
      {"category": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["productOffering"]}},
      {"relatedParty": {$present: ["role"]}},
      {"qualificationItemRelationship": {$present: ["type", "id"]}},
      {"productRelationship": {$present: ["type", "id"]}},
      {"productCharacteristic": {$present: ["name", "value"]}},
      {"productSpecification": {$eitherOf: ["id", "href"]}},
      {"channel": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["productOfferingQualificationItem"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "productOfferingQualificationDateTime", "effectiveQualificationDate"]}},
      {"productOfferingQualificationItem": {$present: ["category", "productOffering", "product"]}},
      {"productOffering": {$eitherOf: ["id", "href"]}},
      {"category": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["productOffering"]}},
      {"relatedParty": {$present: ["role"]}},
      {"qualificationItemRelationship": {$present: ["type", "id"]}},
      {"productRelationship": {$present: ["type", "id"]}},
      {"productCharacteristic": {$present: ["name", "value"]}},
      {"productSpecification": {$eitherOf: ["id", "href"]}},
      {"channel": {$eitherOf: ["id", "href"]}}
    ],
  },

  "AppliedCustomerBillingRate": {
    "operations": ["GET"],
  },

  "Service": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"serviceOrder": {$eitherOf: ["id", "href"]}},
      {"serviceSpecification": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {"serviceRelationship": {$present: ["type"]}},
      {"serviceRelationship.serviceRef": {$eitherOf: ["id", "href"]}},
      {"supportingService": {$eitherOf: ["id", "href"]}},
      {"supportingResource": {$eitherOf: ["id", "href"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}},
      {$: {$present: ["name", "relatedParty"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "orderDate"]}},
      {"serviceOrder": {$eitherOf: ["id", "href"]}},
      {"serviceSpecification": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {"serviceRelationship": {$present: ["type"]}},
      {"serviceRelationship.serviceRef": {$eitherOf: ["id", "href"]}},
      {"supportingService": {$eitherOf: ["id", "href"]}},
      {"supportingResource": {$eitherOf: ["id", "href"]}},
      {"note": {$present: ["text"]}},
      {"place": {$present: ["role"]}}
    ],
  },

  "TroubleTicket": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {$: {$present: ["description", "severity", "ticketType"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "creationDate", "lastUpdated", "statusChange", "@baseType", "@type", "@schemaLocation"]}},
      
    ],
  },

  "AvailabilityCheck": {
    "operations": ["POST"],
    "POST": [
      
    ],
    "PATCH": [
      
    ],
  },

  "ProductSpecification": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  },

  "Quote": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"quoteItem": {$present: ["id"]}},
      {"quoteItem": {$present: ["action"]}},
      {"quoteItem.quoteItem": {$present: ["id", "action"]}},
      {"note": {$present: ["text"]}},
      {"agreement": {$eitherOf: ["id", "href"]}},
      {"billingAccount": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {"quoteItem.productOffering": {$eitherOf: ["id", "href"]}},
      {"quoteItem.appointment": {$eitherOf: ["id", "href"]}},
      {"quoteItem.product": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["quoteItem"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "externalId", "version", "quoteDate", "effectiveQuoteCompletionDate", "quoteTotalPrice"]}},
      {"quoteItem": {$present: ["id"]}},
      {"quoteItem": {$present: ["action"]}},
      {"quoteItem.quoteItem": {$present: ["id", "action"]}},
      {"note": {$present: ["text"]}},
      {"agreement": {$eitherOf: ["id", "href"]}},
      {"billingAccount": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"relatedParty": {$present: ["role"]}},
      {"quoteItem.productOffering": {$eitherOf: ["id", "href"]}},
      {"quoteItem.appointment": {$eitherOf: ["id", "href"]}},
      {"quoteItem.product": {$eitherOf: ["id", "href"]}}
    ],
  },

  "Agreement": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {"engagedPartyRole": {$present: ["id", "name"]}},
      {"associatedAgreement": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["name", "type", "engagedPartyRole", "agreementItem"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "completionDate"]}},
      {"engagedPartyRole": {$present: ["id", "name"]}},
      {"associatedAgreement": {$eitherOf: ["id", "href"]}}
    ],
  },

  "EntitySpecification": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "lastUpdate", "@type"]}},
    ],
  },

  "ShoppingCart": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"cartItem": {$present: ["id", "action"]}},
      {"cartItem.cartItem": {$present: ["id", "action"]}},
      {"cartItem.note": {$present: ["text"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"cartItem.product.place": {$present: ["role", "href"]}},
      {"cartItem.productOffering": {$eitherOf: ["id", "href"]}},
      {"cartItem.product": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["cartItem"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "validFor", "cartTotalPrice"]}},
      {"cartItem": {$present: ["id", "action"]}},
      {"cartItem.cartItem": {$present: ["id", "action"]}},
      {"cartItem.note": {$present: ["text"]}},
      {"relatedParty": {$present: ["name"]}},
      {"relatedParty": {$eitherOf: ["id", "href"]}},
      {"cartItem.product.place": {$present: ["role"]}},
      {"cartItem.productOffering": {$eitherOf: ["id", "href"]}},
      {"cartItem.product": {$eitherOf: ["id", "href"]}}
    ],
  },

  "ServiceLevelObjective": {
    "operations": ["GET", "PATCH", "POST", "DELETE"],
    "POST": [
      {"specParameter": {$present: ["name", "relatedEntity"]}},
      {"specParameter.relatedEntity": {$eitherOf: ["id", "href"]}},
      {$: {$present: ["conformanceTarget"]}},
      {$: {$present: ["conformanceComparator"]}},
      {$: {$present: ["specParameter"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "validFor"]}},
      {"specParameter": {$present: ["name", "relatedEntity"]}},
      {"specParameter.relatedEntity": {$eitherOf: ["id", "href"]}}
    ],
  },

  "ProductOffering": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}},
      {"isBundle": {$equal: "true", $present: "bundledProductOffering"}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href", "lastUpdate"]}},
    ],
  },

  "EntityCategory": {
    "operations": ["GET", "POST", "PATCH", "DELETE"],
    "POST": [
      {$: {$present: ["name"]}}
    ],
    "PATCH": [
      {$: {$noneOf: ["id", "href"]}},
    ],
  }
};


module.exports = { validationRules, validationRulesType2 };
