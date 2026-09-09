permit(
  principal,
  action == AgentCore::Action::"AwsSecOpsPilotV1Read___check_security_group",
  resource == AgentCore::Gateway::"<GATEWAY_ARN>"
)
when {
  context.input.environment == "dev"
};
