export interface TmfCatalogComponent {
  name: string
  code?: string
  aliases?: string[]
}

export interface TmfCatalogDomain {
  key: string
  title: string
  components: TmfCatalogComponent[]
}

export const TMF_COMPONENT_CATALOG: TmfCatalogDomain[] = [
  {
    key: 'party-management',
    title: 'Party Management',
    components: [
      { name: 'Agreement Management', code: 'TMFC039', aliases: ['agreementmanagement'] },
      { name: 'Bill Generation Management', code: 'TMFC030', aliases: ['billgenerationmanagement'] },
      {
        name: 'Billing Account Management',
        code: 'TMFC024',
        aliases: ['billingaccountmanagement', 'billingaccount'],
      },
      {
        name: 'Billing Inquiries Management',
        code: 'TMFC025',
        aliases: ['billinginquiriesmanagement', 'billinginquirymanagement'],
      },
      { name: 'Campaign Management', code: 'TMFC057', aliases: ['campaignmanagement'] },
      { name: 'Debt Collection Management', code: 'TMFC026', aliases: ['debtcollectionmanagement'] },
      {
        name: 'Digital Identity Management',
        code: 'TMFC020',
        aliases: ['digitalidentitymanagement', 'identitymanagement'],
      },
      { name: 'Document Management', code: 'TMFC051', aliases: ['documentmanagement'] },
      {
        name: 'Finance Accounting Management',
        aliases: ['financeaccountingmanagement', 'accountingmanagement'],
      },
      {
        name: 'Lead & Opportunity Management',
        code: 'TMFC036',
        aliases: ['leadopportunitymanagement', 'leadandopportunitymanagement'],
      },
      {
        name: 'Marketing Communications',
        code: 'TMFC049',
        aliases: ['marketingcommunications'],
      },
      {
        name: 'Party Interaction Management',
        code: 'TMFC023',
        aliases: ['partyinteractionmanagement'],
      },
      { name: 'Party Management', code: 'TMFC028', aliases: ['partymanagement'] },
      { name: 'Party Privacy Management', code: 'TMFC022', aliases: ['partyprivacymanagement'] },
      { name: 'Party Problem Management', code: 'TMFC047', aliases: ['partyproblemmanagement'] },
      { name: 'Payment Management', code: 'TMFC029', aliases: ['paymentmanagement'] },
      {
        name: 'Party Roles Permissions Management',
        code: 'TMFC035',
        aliases: [
          'partyrolespermissionsmanagement',
          'partyrolespermissionsmgt',
          'partyrolespermissions',
          'userrolesandpermissions',
        ],
      },
      {
        name: 'Sales Strategy & Planning',
        code: 'TMFC048',
        aliases: ['salesstrategyplanning', 'salesstrategyandplanning'],
      },
    ],
  },
  {
    key: 'core-commerce-management',
    title: 'Core Commerce Management',
    components: [
      { name: 'Bill Calculation', code: 'TMFC031', aliases: ['billcalculation'] },
      { name: 'Commission Management', code: 'TMFC059', aliases: ['commissionmanagement'] },
      {
        name: 'Product Assurance Management',
        aliases: ['productassurancemanagement'],
      },
      {
        name: 'Product Catalog Management',
        code: 'TMFC001',
        aliases: ['productcatalogmanagement', 'productcatalog'],
      },
      {
        name: 'Product Configurator',
        code: 'TMFC027',
        aliases: ['productconfigurator'],
      },
      { name: 'Product Inventory', code: 'TMFC005', aliases: ['productinventory'] },
      {
        name: 'Product Order Capture & Validation',
        code: 'TMFC002',
        aliases: [
          'productordercapturevalidation',
          'productordercaptureandvalidation',
          'productordercapture',
        ],
      },
      {
        name: 'Product Order Delivery Orch & Mgt',
        code: 'TMFC003',
        aliases: [
          'productorderdeliveryorchestrationmanagement',
          'productorderdeliveryorchmgt',
          'productorderdeliverymanagement',
        ],
      },
      {
        name: 'Product Recommendation Management',
        code: 'TMFC050',
        aliases: ['productrecommendationmanagement', 'productrecommendation', 'productrec'],
      },
      {
        name: 'Product Test Management',
        code: 'TMFC054',
        aliases: ['producttestmanagement'],
      },
      {
        name: 'Product Usage Management',
        code: 'TMFC040',
        aliases: ['productusagemanagement'],
      },
      {
        name: 'Product / Sales Performance Management',
        code: 'TMFC058',
        aliases: ['productsalesperformancemanagement', 'salesperformancemanagement'],
      },
      { name: 'Purchase Management', code: 'TMFC033', aliases: ['purchasemanagement'] },
    ],
  },
  {
    key: 'production',
    title: 'Production',
    components: [
      { name: 'Anomaly Management', code: 'TMFC041', aliases: ['anomalymanagement'] },
      { name: 'Fault Management', code: 'TMFC043', aliases: ['faultmanagement'] },
      {
        name: 'IT and Network Infrastructure Management',
        code: 'TMFC052',
        aliases: ['itandnetworkinfrastructuremanagement', 'networkinfrastructuremanagement'],
      },
      { name: 'Location Management', code: 'TMFC014', aliases: ['locationmanagement'] },
      {
        name: 'Resource Capability Delivery',
        aliases: ['resourcecapabilitydelivery'],
      },
      {
        name: 'Resource Catalog Management',
        code: 'TMFC010',
        aliases: ['resourcecatalogmanagement'],
      },
      {
        name: 'Resource Configuration and Activation',
        code: 'TMFC062',
        aliases: ['resourceconfigurationandactivation'],
      },
      {
        name: 'Resource Discovery and Reconciliation',
        code: 'TMFC045',
        aliases: ['resourcediscoveryandreconciliation'],
      },
      { name: 'Resource Inventory', code: 'TMFC012', aliases: ['resourceinventory'] },
      {
        name: 'Resource Order Management',
        code: 'TMFC011',
        aliases: ['resourceordermanagement'],
      },
      {
        name: 'Resource Performance Management',
        code: 'TMFC038',
        aliases: ['resourceperformancemanagement', 'resourceperformancemgt'],
      },
      {
        name: 'Resource Test Management',
        code: 'TMFC056',
        aliases: ['resourcetestmanagement'],
      },
      {
        name: 'Resource Usage Management',
        code: 'TMFC016',
        aliases: ['resourceusagemanagement'],
      },
      {
        name: 'Service Balance Management',
        code: 'TMFC013',
        aliases: ['servicebalancemanagement'],
      },
      {
        name: 'Service Catalog Management',
        code: 'TMFC006',
        aliases: ['servicecatalogmanagement'],
      },
      { name: 'Service Inventory', code: 'TMFC008', aliases: ['serviceinventory'] },
      {
        name: 'Service Order Management',
        code: 'TMFC007',
        aliases: ['serviceordermanagement'],
      },
      {
        name: 'Service Performance Management',
        code: 'TMFC037',
        aliases: ['serviceperformancemanagement', 'serviceperformancemgt'],
      },
      {
        name: 'Service Qualification Management',
        code: 'TMFC009',
        aliases: ['servicequalificationmanagement'],
      },
      {
        name: 'Service Quality Management',
        code: 'TMFC053',
        aliases: ['servicequalitymanagement'],
      },
      {
        name: 'Service Test Management',
        code: 'TMFC055',
        aliases: ['servicetestmanagement'],
      },
      {
        name: 'Service Usage Management',
        code: 'TMFC015',
        aliases: ['serviceusagemanagement'],
      },
      {
        name: 'Strategic Resource Planning',
        code: 'TMFC044',
        aliases: ['strategicresourceplanning'],
      },
      {
        name: 'Supply Chain Management',
        code: 'TMFC032',
        aliases: ['supplychainmanagement'],
      },
      {
        name: 'Work Order Management',
        code: 'TMFC061',
        aliases: ['workordermanagement'],
      },
      {
        name: 'Workforce Management',
        code: 'TMFC046',
        aliases: ['workforcemanagement'],
      },
    ],
  },
]

// ---------------------------------------------------------------------------
// Canvas Operators catalog
// ---------------------------------------------------------------------------
// Static mirror of https://www.tmforum.org/oda/directory/components-map left
// rail (Canvas Operator section). Used by ComponentTopology to render an
// "Installed / Not installed" tile per operator. Entries without a `code` are
// listed in the TMF directory but have not been assigned a TMFOP id yet.
//
// `signatureKey` matches the canonical operator name produced by the backend
// _discover_logical_operators / OPERATOR_SIGNATURES (see
// backend/k8s/resources/operators.py). Multiple catalog entries may share a
// signatureKey when a single cluster operator implements multiple TMF roles
// (e.g. the kong/istio API gateway), and a single TMF code may map to several
// signatureKeys for the same reason.

export interface TmfOperatorCatalogEntry {
  name: string
  code?: string
  /** Canonical operator names (from OPERATOR_SIGNATURES) that satisfy this entry. */
  signatureKeys?: string[]
}

export const TMF_OPERATOR_CATALOG: TmfOperatorCatalogEntry[] = [
  { name: 'Component Management Operator',         code: 'TMFOP001', signatureKeys: ['component-operator'] },
  { name: 'API Management Operator',               code: 'TMFOP002', signatureKeys: ['api-operator-istio', 'api-operator-kong', 'api-operator-apisix'] },
  { name: 'Identity Configuration Operator',       code: 'TMFOP003', signatureKeys: ['identityconfig-operator-keycloak'] },
  { name: 'Credentials Management Operator',       code: 'TMFOP004' },
  { name: 'Dependency Management Operator',        code: 'TMFOP005' },
  { name: 'Event Management Operator',             code: 'TMFOP006' },
  { name: 'Secrets Management Operator',           code: 'TMFOP007', signatureKeys: ['secretsmanagement-operator'] },
  { name: 'oauth2 Configuration Operator',         code: 'TMFOP008' },
  { name: 'Model-as-a-Service Operator',           code: 'TMFOP009', signatureKeys: ['modelgateway-ai-gateway-operator', 'ai-gateway-operator'] },
  { name: 'Disruption Budget Management Operator', code: 'TMFOP010', signatureKeys: ['pdb-management-operator'] },
  { name: 'Carbon Management Operator',            code: 'TMFOP011' },
  { name: 'Cost Control Operator' },
  { name: 'Database Management Operator' },
  { name: 'Enterprise Integration Operator' },
]
