# Nexus

A modern cloud-based application for efficiently managing resources and operations using AWS SAM.

## Setup

1. Install mise: https://mise.jdx.dev/
2. Run `mise install` to set up the Python environment
3. Run `uv pip install -e .` to install the package
4. Install AWS SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

## Development

```
uv pip install -e ".[dev]"
```

## Deployment

```
# Build the SAM application
sam build

# Deploy the application
sam deploy --guided
```

## Local Testing

```
sam local invoke -e events/event.json <function-name>
sam local start-api
``` 