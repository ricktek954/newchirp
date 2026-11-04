# myGMRS API integration

Last checked: 2026-11-04

The myGMRS developer portal documents a JSON API at
`https://api.mygmrs.com`. NewChirp uses OAuth 2.0 Authorization Code with
PKCE S256 and requests only the `repeaters:read` scope.

Official references:

- Developer portal: `https://developers.mygmrs.com/`
- OAuth guide: `https://developers.mygmrs.com/oauth`
- Redirect URI rules: `https://developers.mygmrs.com/oauth/redirect-uris`
- Repeater API: `https://developers.mygmrs.com/reference/repeaters`

## Client configuration

- Public client ID: `mg_wiOzRfSIVvZYjwvgBUyH_u6U`
- NewChirp requests no client secret. A public desktop client must not ship one.
- Default API base: `https://api.mygmrs.com`
- Requested scope: `repeaters:read`

The client ID is public OAuth configuration, not a password. It can be
overridden at build time:

```sh
flutter build macos --release \
  --dart-define=MYGMRS_CLIENT_ID=mg_wiOzRfSIVvZYjwvgBUyH_u6U \
  --dart-define=MYGMRS_REDIRECT_URI=http://127.0.0.1:8765/callback
```

## Desktop callback

myGMRS recommends loopback callbacks for desktop and CLI clients. NewChirp
defaults to:

```text
http://127.0.0.1:8765/callback
```

The app listens only on IPv4 loopback while the system browser performs
myGMRS sign-in. The listener validates the OAuth `state`, accepts the
one-time code, and closes. myGMRS matches the complete redirect string,
including scheme, host, port, and path; it does not support wildcard ports.

The supplied client currently has the custom callback
`net.newchirp.newchirp_mobile:/mygmrs/callback` registered, but not the
loopback callback. Live sign-in therefore remains blocked until the loopback
URI above is registered for this client. The custom URI is not the default
because its scheme contains an underscore and would also require native
URL-handler registration on macOS, Windows, and Linux.

## Token handling

- Access tokens and rotating refresh tokens remain in memory for the life of
  the running NewChirp process.
- Tokens and authorization codes are never written to diagnostics or logs.
- Tokens are not currently persisted across application restarts. This avoids
  storing refresh tokens in plaintext while cross-platform secure storage is
  not yet implemented.
- Concurrent refresh requests are not possible in the current UI because one
  shared myGMRS client performs refreshes serially.

## Repeater search

NewChirp calls:

```text
GET https://api.mygmrs.com/repeaters
```

It sends the US state abbreviation, optional text query, optional coordinates
and radius, `description=true`, `offline=false`, `limit=100`, and `skip=0`.
The UI radius is entered in kilometers and converted to miles because the API
uses miles.

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

## Next verification

1. Register `http://127.0.0.1:8765/callback` for the existing client.
2. Sign in with an active, non-Premium GMRS account and verify that frequency,
   name, location, and map data import while PL tones remain absent.
3. Repeat with a Premium account and verify PL In, PL Out, and rules.
4. Confirm the loopback listener closes after success, denial, timeout, and an
   invalid `state`.
5. Decide whether refresh tokens should move to Keychain, DPAPI, and libsecret
   after a secure-storage implementation is available for all desktop targets.
