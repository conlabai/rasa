# rasa-nlg-server

This is an optional server you can use to do additional processing on Natural Language Generation.
The example nlg server here supports using canned responses from Chatwoot.

## Environment variables

### `CHATWOOT_URL` (string)
  
  An URL pointing to the Chatwoot API to get canned responses. Defaults to "http://localhost:3000"

### `CHATWOOT_API_KEY` (string)

  A token allowing fetching canned responses

### `NLG_DEBUG`

  Any non-empty value turns debugging on, default: no debugging (production mode)

### `NLG_AUTO_RELOAD`
  
  Any non-empty value turns auto-reloading on (for development), default: no reloading

### `NLG_CHATWOOT_REFRESH_SECONDS` (int)
  
  When the Chatwoot canned responses are older than this number of seconds, they will be fetched again from Chatwoot. Default: 60.

### `NLG_DOMAIN_PATH` (string)
  
  NLG server will try to read the domain file using this path, if the path is set. If not, it will try to connect to `RASA_URL` and request the domain from the RASA API.

### `RASA_URL` (string)

  An URL pointing to a Rasa endpoint for fetching the domain data. Default: "http://localhost:5005".

### `SANIC_BACKLOG` (int)
  
  A number of unaccepted connections that the system will allow before refusing new connections.
