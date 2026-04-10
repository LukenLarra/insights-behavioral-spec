Feature: AI-powered Upgrade Risks Prediction validation for CCX Data Engineering
  As a tester
  I want to use AI to validate complex upgrade risk prediction responses
  So that I can verify business logic, schema and semantic correctness without rigid custom assertions

  Background: Data eng service is running and well configured to work
    Given The mock CCX Inference Service is running on port 9090
      And The mock RHOBS Service is running on port 9091
      And The CCX Data Engineering Service is running on port 8000 with envs
          | variable                    | value                                  |
          | CLIENT_ID                   | test-client-id                         |
          | CLIENT_SECRET               | test-client-secret                     |
          | INFERENCE_URL               | http://localhost:9090                  |
          | SSO_ISSUER                  | http://mock-oauth2-server:8081/default |
          | ALLOW_INSECURE              | 1                                      |
          | RHOBS_URL                   | http://localhost:9091                  |
          | OAUTHLIB_INSECURE_TRANSPORT | 1                                      |

  @llm
  Scenario: Verify a risky cluster prediction is explained coherently by the response
    When I request the cluster endpoint in localhost:8000 with path aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/upgrade-risks-prediction
    Then The status code of the response is 200
     And the LLM confirms that "upgrade_recommended is false and there is at least one critical alert in upgrade_risks_predictors.alerts justifying the decision"

  @llm
  Scenario: Validate that duplicate alerts are removed from the response
    When I request the cluster endpoint in localhost:8000 with path 44444444-3333-2222-1111-111111111111/upgrade-risks-prediction
    Then The status code of the response is 200
     And the LLM confirms that "the alerts array contains no duplicate entries — each alert name and namespace combination appears only once"

  @llm
  Scenario: Validate that the FOC condition is mapped to a human readable value
    When I request the cluster endpoint in localhost:8000 with path aaaaaaaa-bbbb-cccc-dddd-000000000000/upgrade-risks-prediction
    Then The status code of the response is 200
     And the LLM confirms that "the operator_conditions array contains a condition with value 'Not Available', which is a human readable mapping of a FOC condition"

  @llm
  Scenario: Validate upgrade risk response schema and types using AI
    When I request the cluster endpoint in localhost:8000 with path aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/upgrade-risks-prediction
    Then The status code of the response is 200
     And the LLM confirms that "the response object contains upgrade_recommended (boolean), upgrade_risks_predictors (object with alerts and operator_conditions arrays), and last_checked_at (string), and each alert and operator_condition has appropriately typed fields"

  @llm
  Scenario: Validate invalid cluster ID error handling without exposing sensitive data
    When I request the cluster endpoint in localhost:8000 with path not-an-uuid/upgrade-risks-prediction
    Then The status code of the response is 422
     And the LLM confirms that no sensitive data is exposed in the response

  @llm
  Scenario: Validate missing cluster version returns a meaningful 404 with AI
    When I request the cluster endpoint in localhost:8000 with path 00000000-1111-2222-3333-444444444444/upgrade-risks-prediction
    Then The status code of the response is 404
     And the LLM confirms that "the response indicates that no data was found for the requested cluster, without exposing internal implementation details"
