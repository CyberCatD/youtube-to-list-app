# Gemini CLI Configuration

This file stores custom configurations for the Gemini CLI to enhance usability and efficiency.

## Best Practice Settings for New Users

These settings are recommended for a smooth and productive experience, especially when you are new to the tool.

### Output and Logging
- `output_format`: `json`
  - **Description**: Ensures consistent, machine-readable output, which is ideal for scripting and integrating with other tools.
- `log_level`: `info`
  - **Description**: Provides a good balance of operational details without being overly verbose. Useful for debugging and understanding the CLI's actions.

### Operational Settings
- `no_prompt_on_exit`: `true`
  - **Description**: Disables confirmation prompts before exiting the CLI. This streamlines workflows and scripting.
- `max_retries`: `5`
  - **Description**: Automatically retries operations up to 5 times in case of transient network issues or temporary service unavailability.
- `timeout_seconds`: `60`
  - **Description**: Sets a default timeout of 60 seconds for operations, preventing them from hanging indefinitely.

## Usage Examples

### Setting a value
`gemini config set output_format json`

### Viewing all settings
`gemini config list`

### Applying settings to a command
`gemini command --option value`