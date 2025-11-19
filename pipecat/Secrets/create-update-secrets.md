# Create or Update Secrets

> Create or update a secret set and its values

## OpenAPI

````yaml PUT /secrets/{setName}
paths:
  path: /secrets/{setName}
  method: put
  servers:
    - url: https://api.pipecat.daily.co/v1
      description: API server
  request:
    security:
      - title: PrivateKeyAuth
        parameters:
          query: {}
          header:
            Authorization:
              type: http
              scheme: bearer
              description: >-
                Authentication requires a Pipecat Cloud Private API token.


                Generate a Private API key from your Dashboard (Settings > API
                Keys > Private > Create key) and include it as a Bearer token in
                the Authorization header.
          cookie: {}
    parameters:
      path:
        setName:
          schema:
            - type: string
              required: true
              description: Name of the secret set to create or update
              maxLength: 63
              minLength: 3
      query: {}
      header: {}
      cookie: {}
    body:
      application/json:
        schemaArray:
          - type: object
            properties:
              secrets:
                allOf:
                  - type: array
                    items:
                      type: object
                      properties:
                        secretKey:
                          type: string
                          description: Name of the secret key
                        secretValue:
                          type: string
                          description: Value of the secret
                      required:
                        - secretKey
                        - secretValue
                    minItems: 1
                    description: Array of secret key-value pairs
            required: true
            refIdentifier: '#/components/schemas/RegularSecretsRequest'
            requiredProperties:
              - secrets
          - type: object
            properties:
              isImagePullSecret:
                allOf:
                  - type: boolean
                    enum:
                      - true
                    description: Must be true for image pull secrets
              host:
                allOf:
                  - type: string
                    format: uri
                    description: Host URL
                    example: https://index.docker.io/v1/
              secretValue:
                allOf:
                  - type: string
                    description: Authentication token or credentials
            required: true
            refIdentifier: '#/components/schemas/ImagePullSecretRequest'
            requiredProperties:
              - isImagePullSecret
              - host
              - secretValue
        examples:
          regularSecrets:
            summary: Regular secrets
            description: Create or update a set with multiple key-value pairs
            value:
              secrets:
                - secretKey: API_KEY
                  secretValue: your-api-key
                - secretKey: DATABASE_URL
                  secretValue: postgresql://user:pass@host:5432/db
          imagePullSecret:
            summary: Image pull secret
            description: Create an image pull secret
            value:
              isImagePullSecret: true
              host: https://index.docker.io/v1/
              secretValue: your-docker-auth-token
  response:
    '200':
      application/json:
        schemaArray:
          - type: object
            properties:
              status:
                allOf:
                  - type: string
                    enum:
                      - OK
        examples:
          example:
            value:
              status: OK
        description: Secret set successfully created or updated
    '400':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - &ref_0
                    type: string
                    description: Error message
              code:
                allOf:
                  - &ref_1
                    type: string
                    description: Error code
            refIdentifier: '#/components/schemas/ErrorResponse'
        examples:
          cannotUpdateImagePullSecret:
            summary: Cannot update existing image pull secrets
            value:
              error: >-
                Cannot update existing image pull secrets. Delete and recreate
                instead.
              code: GENERIC_BAD_REQUEST
          validationError:
            summary: Validation error
            value:
              error: Invalid request format
              code: GENERIC_BAD_REQUEST
        description: Bad request - Invalid parameters or operation not allowed
    '401':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
              code:
                allOf:
                  - *ref_1
            refIdentifier: '#/components/schemas/ErrorResponse'
        examples:
          example:
            value:
              error: Unauthorized
              code: UNAUTHORIZED
        description: Unauthorized - Invalid or missing API key
    '500':
      application/json:
        schemaArray:
          - type: object
            properties:
              error:
                allOf:
                  - *ref_0
              code:
                allOf:
                  - *ref_1
            refIdentifier: '#/components/schemas/ErrorResponse'
        examples:
          example:
            value:
              error: <string>
              code: <string>
        description: Internal server error
  deprecated: false
  type: path
components:
  schemas: {}

````