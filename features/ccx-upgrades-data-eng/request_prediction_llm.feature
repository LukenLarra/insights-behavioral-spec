@ccx_data_engineering
Feature: LLM-based semantic assertions for upgrade risk predictions

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
  Scenario: LLM validates that a risky prediction coherently justifies not upgrading
    When I request the cluster endpoint in localhost:8000 with path aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/upgrade-risks-prediction
    Then The status code of the response is 200
     And the LLM confirms that "upgrade_recommended is false and there is at least one critical alert in upgrade_risks_predictors.alerts justifying the decision"

  @llm
  Scenario: LLM validates that duplicate alerts are removed from the response
    When I request the cluster endpoint in localhost:8000 with path 44444444-3333-2222-1111-111111111111/upgrade-risks-prediction
    Then The status code of the response is 200
     And the LLM confirms that "the alerts array contains no duplicate entries — each alert name and namespace combination appears only once"

  @llm
  Scenario: LLM validates that the FOC condition is mapped to a human readable value
    When I request the cluster endpoint in localhost:8000 with path aaaaaaaa-bbbb-cccc-dddd-000000000000/upgrade-risks-prediction
    Then The status code of the response is 200
     And the LLM confirms that "the operator_conditions array contains a condition with value 'Not Available', which is a human readable mapping of a FOC condition"

  @llm
  Scenario: LLM validates that an invalid UUID receives a clear error response
    When I request the cluster endpoint in localhost:8000 with path not-an-uuid/upgrade-risks-prediction
    Then The status code of the response is 422
     And the LLM confirms that no sensitive data is exposed in the response

  @llm
  Scenario: LLM validates that a missing cluster version returns a meaningful 404
    When I request the cluster endpoint in localhost:8000 with path 00000000-1111-2222-3333-444444444444/upgrade-risks-prediction
    Then The status code of the response is 404
     And the LLM confirms that "the response indicates that no data was found for the requested cluster, without exposing internal implementation details"