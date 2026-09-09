permit(
  principal,
  action == AgentCore::Action::"AwsSecOpsPilotV1S3Read___check_s3_baseline",
  resource == AgentCore::Gateway::"<GATEWAY_ARN>"
)
when {
  context.input.environment == "dev"
};
