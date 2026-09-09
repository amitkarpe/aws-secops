permit(
  principal,
  action == AgentCore::Action::"AwsSecOpsP0B3Target___check_demo_scope",
  resource == AgentCore::Gateway::"<GATEWAY_ARN>"
)
when {
  context.input.environment == "dev"
};
