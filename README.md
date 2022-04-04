# transmogrifier
Data transformation CLI app for TIMDEX

## Development
To install with dev dependencies:
```
make install
```
To run unit tests:
```
make test
```

To install lint the repo:
```
make lint
```
 
To install run the app:
```
pipenv run transform <command>
```

## Required ENV
`SENTRY_DSN` = if set to a valid Sentry DSN, enables Sentry exception monitoring