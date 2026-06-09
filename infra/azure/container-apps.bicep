param location string = resourceGroup().location
param environmentName string = 'nexusmind-enterprise-env'
param apiImage string
param webImage string
param jwtSecret string
param postgresDsn string
param mongoUri string
param redisUrl string
param qdrantUrl string
param neo4jUri string
param kafkaBootstrapServers string
param sparkMasterUrl string

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${environmentName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: toLower(replace('${environmentName}ai', '-', ''))
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'nexusmind-api'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        {
          name: 'jwt-secret'
          value: jwtSecret
        }
        {
          name: 'postgres-dsn'
          value: postgresDsn
        }
        {
          name: 'mongo-uri'
          value: mongoUri
        }
        {
          name: 'redis-url'
          value: redisUrl
        }
        {
          name: 'neo4j-uri'
          value: neo4jUri
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          env: [
            {
              name: 'JWT_SECRET_KEY'
              secretRef: 'jwt-secret'
            }
            {
              name: 'POSTGRES_DSN'
              secretRef: 'postgres-dsn'
            }
            {
              name: 'MONGO_URI'
              secretRef: 'mongo-uri'
            }
            {
              name: 'REDIS_URL'
              secretRef: 'redis-url'
            }
            {
              name: 'QDRANT_URL'
              value: qdrantUrl
            }
            {
              name: 'NEO4J_URI'
              secretRef: 'neo4j-uri'
            }
            {
              name: 'KAFKA_BOOTSTRAP_SERVERS'
              value: kafkaBootstrapServers
            }
            {
              name: 'SPARK_MASTER_URL'
              value: sparkMasterUrl
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT'
              value: storage.name
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
      }
    }
  }
}

resource web 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'nexusmind-web'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
      }
    }
    template: {
      containers: [
        {
          name: 'web'
          image: webImage
          env: [
            {
              name: 'NEXT_PUBLIC_API_BASE_URL'
              value: 'https://${api.properties.configuration.ingress.fqdn}/api/v1'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
      }
    }
  }
}

output apiUrl string = 'https://${api.properties.configuration.ingress.fqdn}'
output webUrl string = 'https://${web.properties.configuration.ingress.fqdn}'
output logAnalyticsWorkspace string = logs.name
output storageAccountName string = storage.name
