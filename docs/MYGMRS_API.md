# myGMRS API integration

Last checked: 2026-11-05

The myGMRS developer portal documents a JSON API at
`https://api.mygmrs.com`. NewChirp uses OAuth 2.0 Authorization Code with
PKCE S256 and requests only the `repeaters:read` scope.

The myGMRS directory is enabled. myGMRS approved the confidential
server-side client and registered the NewChirp callback on 2026-11-05.

Official references:

- Developer portal: `https://developers.mygmrs.com/`
- OAuth guide: `https://developers.mygmrs.com/oauth`
- Redirect URI rules: `https://developers.mygmrs.com/oauth/redirect-uris`
- Repeater API: `https://developers.mygmrs.com/reference/repeaters`

## Client configuration

- Confidential web client ID: `mg_smZAkkxFZZ7_4vFQH6puaP0h`
- The client secret exists only in the `newchirp.net` server environment. It
  is never included in desktop builds, responses, diagnostics, or logs.
- NewChirp no longer sends myGMRS API requests or OAuth tokens from the desktop.
- Requested scope: `repeaters:read`

The client ID is public OAuth configuration, not a password. It can be
overridden at build time:

```sh
flutter build macos --release \
  --dart-define=MYGMRS_BROKER_BASE=https://newchirp.net
```

## Website-mediated desktop callback

NewChirp may run behind a firewall, so the app does not host an inbound OAuth
listener. The newchirp.net website provides the public callback:

```text
https://newchirp.net/api/mygmrs/oauth/callback
```

The app:

1. Calls `POST https://newchirp.net/api/mygmrs/oauth/start`.
2. Opens the returned myGMRS authorization URL in the system browser.
3. Polls `POST https://newchirp.net/api/mygmrs/oauth/poll` with a random,
   short-lived bearer handoff token.
4. Receives an opaque NewChirp session token after the website exchanges the
   code.

The website creates the PKCE verifier and `state`, validates and consumes
`state`, exchanges the authorization code with the confidential client secret,
and keeps myGMRS access and refresh tokens in process memory. Authorization
codes, myGMRS tokens, and the client secret are never placed in browser URLs or
returned to the desktop.

myGMRS registered the website callback above for the confidential client. The
custom URI suggested in Rich's email was only an example and is not used.

## Token handling

- myGMRS access and rotating refresh tokens remain server-side in the
  `newchirp.net` process.
- The desktop receives only an opaque NewChirp session token. It does not
  receive myGMRS tokens.
- The relay refreshes expiring myGMRS access tokens and serializes concurrent
  refreshes.
- Sessions expire after 12 hours without use. Server restart invalidates them.
- Sign-out invalidates the NewChirp session and revokes the myGMRS refresh
  token.
- Tokens, authorization codes, and the client secret are never written to
  diagnostics or logs.

## Repeater search

NewChirp calls:

```text
POST https://newchirp.net/api/mygmrs/repeaters/search
```

The request is authenticated with the opaque NewChirp session. The website adds
the server-held myGMRS access token, refreshes it when needed, and proxies
`GET https://api.mygmrs.com/repeaters`. The desktop sends the US state
abbreviation, optional text query, optional coordinates and radius, and the
result limit. The UI radius is entered in kilometers and converted to miles
because the API uses miles.

The API omits repeater frequencies for anonymous callers and for signed-in
users without an active GMRS license. PL tones and rules require both the
`repeaters:read` scope and an active Premium membership. NewChirp reports
this distinction instead of silently importing incomplete channels.

## Channel mapping

- Frequency: myGMRS repeater output frequency
- Duplex: `+5 MHz` for GMRS repeater outputs from 462.550 through 462.725 MHz
- TX tone: `PL In`
- RX tone: `PL Out`
- Mode: FM
- Name, location, state, coordinates, online status, owner, travel-tone,
  ORI/open-system status, and available rules

If PL In and PL Out match, the channel uses TSQL. If only PL In exists, it
uses transmit Tone. If they differ, it uses a Tone-to-Tone cross mode. Missing
Premium tones do not block importing the licensed frequency.

## Remaining verification

1. Sign in with an active, non-Premium GMRS account and verify that frequency,
   name, location, and map data import while PL tones remain absent.
2. Repeat with a Premium account and verify PL In, PL Out, and rules.
3. Confirm sign-out revokes the upstream token and all server-side session
   records.
