# mygmrs_client

## Classs

- [_JsonResponse](JsonResponse.md)
- [MyGmrsException](MyGmrsException.md)
- [MyGmrsService](MyGmrsService.md)

## Functions

- [_apiError](apiError.md) — Opens [uri] in the default browser (open / rundll32 / xdg-open).
- [_applyTones](applyTones.md) — Sets tone mode: same tone both ways = TSQL, transmit only = Tone,
- [_ctcssTone](ctcssTone.md) — First number in a tone value such as "141.3 Hz" or "PL 100.0".
- [_gmrsRepeaterOutput](gmrsRepeaterOutput.md) — True for the GMRS repeater output channels 462.550-462.725 MHz (inputs are +5 MHz).
- [_jsonRequest](jsonRequest.md) — One HTTP request to the website with a 20-second connect timeout; returns
- [_openSystemBrowser](openSystemBrowser.md) — Opens [uri] in the default browser (open / rundll32 / xdg-open).
- [_postJson](postJson.md) — POSTs [payload] as JSON to the website and returns the JSON reply; throws on HTTP errors.
- [_stateCode](stateCode.md) — Two-letter code for a US state name (myGMRS searches by code).
- [_storeSession](storeSession.md) — Keeps the session token from the website. It expires after `expiresIn`
- [_throwSignInCancelled](throwSignInCancelled.md) — Throws the "sign-in was cancelled" error.
- [cancelSignIn](cancelSignIn.md) — Opens [uri] in the default browser (open / rundll32 / xdg-open).
- [convertRepeaterResponse](convertRepeaterResponse.md) — Converts the website's JSON into channels: repeater outputs get +5 MHz duplex,
- [ensureSignedIn](ensureSignedIn.md) — Signs in only if there is no unexpired session.
- [MyGmrsClient](MyGmrsClient.md)
- [searchRepeaters](searchRepeaters.md) — Opens [uri] in the default browser (open / rundll32 / xdg-open).
- [signIn](signIn.md) — Opens [uri] in the default browser (open / rundll32 / xdg-open).
- [signOut](signOut.md) — Opens [uri] in the default browser (open / rundll32 / xdg-open).
- [toString](toString.md) — Opens [uri] in the default browser (open / rundll32 / xdg-open).
