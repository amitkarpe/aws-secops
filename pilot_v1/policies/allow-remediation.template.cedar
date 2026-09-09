permit(
  principal,
  action == AgentCore::Action::"AwsSecOpsPilotV1Remediate___remove_unrestricted_ssh",
  resource == AgentCore::Gateway::"<GATEWAY_ARN>"
)
when {
  context.input.environment == "dev" &&
  context.input.approved == true
};
