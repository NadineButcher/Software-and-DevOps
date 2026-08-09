console.log("PASSKEY JS LOADED");

// ============================================================
// WebAuthn Base64URL helpers
// ============================================================

function base64urlToBytes(value) {
    // Make sure we have a string
    if (typeof value !== "string") {
        throw new Error(
            "Expected a Base64URL string."
        );
    }

    // Convert Base64URL to standard Base64
    value = value
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    // Add Base64 padding
    while (value.length % 4 !== 0) {
        value += "=";
    }

    // Decode
    const binary = atob(value);

    return Uint8Array.from(
        binary,
        character => character.charCodeAt(0)
    );
}


function bytesToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);

    let binary = "";

    for (const byte of bytes) {
        binary += String.fromCharCode(byte);
    }

    return btoa(binary)
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=+$/, "");
}


// ============================================================
// PASSKEY REGISTRATION
// ============================================================

window.startRegistration = async function(
    registerStartUrl,
    registerFinishUrl,
    csrfToken
) {
    try {

        const res = await fetch(
            registerStartUrl,
            {
                method: "GET",
                credentials: "same-origin",

                headers: {
                    "Accept": "application/json"
                }
            }
        );

        if (!res.ok) {

            const text = await res.text();

            throw new Error(
                `Registration start failed: ${res.status} ${text}`
            );
        }

        const options = await res.json();

        console.log(
            "Registration options:",
            options
        );

        // Convert WebAuthn binary fields
        options.challenge =
            base64urlToBytes(
                options.challenge
            );

        options.user.id =
            base64urlToBytes(
                options.user.id
            );

        // Convert excluded credential IDs
        if (options.excludeCredentials) {

            options.excludeCredentials =
                options.excludeCredentials.map(
                    credential => ({
                        ...credential,

                        id:
                            base64urlToBytes(
                                credential.id
                            )
                    })
                );
        }

        // Ask the browser to create the passkey
        const credential =
            await navigator.credentials.create({
                publicKey: options
            });

        if (!credential) {
            throw new Error(
                "No passkey credential was created."
            );
        }

        const response = {

            id: credential.id,

            rawId:
                bytesToBase64url(
                    credential.rawId
                ),

            type:
                credential.type,

            response: {

                clientDataJSON:
                    bytesToBase64url(
                        credential.response
                            .clientDataJSON
                    ),

                attestationObject:
                    bytesToBase64url(
                        credential.response
                            .attestationObject
                    )
            }
        };

        const finishResponse =
            await fetch(
                registerFinishUrl,
                {
                    method: "POST",

                    credentials:
                        "same-origin",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "X-CSRFToken":
                            csrfToken,

                        "Accept":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            response
                        )
                }
            );

        const result =
            await finishResponse.json();

        if (!finishResponse.ok) {

            throw new Error(
                result.error ||
                "Passkey registration failed."
            );
        }

        alert(
            "Passkey registered successfully."
        );

    } catch (error) {

        console.error(
            "Passkey registration failed:",
            error
        );

        alert(
            error.message ||
            "Passkey registration failed."
        );

        throw error;
    }
}


// ============================================================
// PASSKEY AUTHENTICATION
// ============================================================

window.startAuth = async function(
    authStartUrl,
    authFinishUrl,
    csrfToken
) {
    try {

        // ----------------------------------------------------
        // Get authentication options from Django
        // ----------------------------------------------------

        const res = await fetch(
            authStartUrl,
            {
                method: "GET",

                credentials:
                    "same-origin",

                headers: {
                    "Accept":
                        "application/json"
                }
            }
        );

        if (!res.ok) {

            const text =
                await res.text();

            throw new Error(
                `Authentication start failed: ${res.status} ${text}`
            );
        }

        const options =
            await res.json();

        console.log(
            "Authentication options:",
            options
        );


        // ----------------------------------------------------
        // Convert challenge
        // ----------------------------------------------------

        options.challenge =
            base64urlToBytes(
                options.challenge
            );


        // ----------------------------------------------------
        // Convert allowed credential IDs
        // ----------------------------------------------------

        if (
            options.allowCredentials &&
            options.allowCredentials.length
        ) {

            options.allowCredentials =
                options.allowCredentials.map(
                    credential => ({
                        ...credential,

                        id:
                            base64urlToBytes(
                                credential.id
                            )
                    })
                );
        }


        // ----------------------------------------------------
        // Ask browser for passkey
        // ----------------------------------------------------

        const credential =
            await navigator.credentials.get({
                publicKey: options
            });

        if (!credential) {

            throw new Error(
                "No passkey credential was returned."
            );
        }


        // ----------------------------------------------------
        // Prepare credential for Django
        // ----------------------------------------------------

        const response = {

            id:
                credential.id,

            rawId:
                bytesToBase64url(
                    credential.rawId
                ),

            type:
                credential.type,

            response: {

                clientDataJSON:
                    bytesToBase64url(
                        credential.response
                            .clientDataJSON
                    ),

                authenticatorData:
                    bytesToBase64url(
                        credential.response
                            .authenticatorData
                    ),

                signature:
                    bytesToBase64url(
                        credential.response
                            .signature
                    ),

                userHandle:
                    credential.response
                        .userHandle
                        ? bytesToBase64url(
                            credential.response
                                .userHandle
                        )
                        : null
            }
        };


        console.log(
            "Sending passkey credential."
        );


        // ----------------------------------------------------
        // Send credential to Django
        // ----------------------------------------------------

        const finishResponse =
            await fetch(
                authFinishUrl,
                {
                    method: "POST",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "X-CSRFToken":
                            csrfToken,

                        "Accept":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            response
                        )
                }
            );

        const responseText = await finishResponse.text();

        console.log(
            "Authentication finish HTTP status:",
            finishResponse.status
        );

        console.log(
            "Authentication finish response:",
            responseText
        );

        let result;

        try {
            result = JSON.parse(responseText);
        } catch (error) {
            throw new Error(
                "Django returned invalid JSON: " +
                responseText
            );
        }

        if (!finishResponse.ok) {

            throw new Error(
                result.error ||
                result.message ||
                "Passkey authentication failed."
            );
        }

        // ----------------------------------------------------
        // Successful authentication
        // ----------------------------------------------------

        console.log(
            "Passkey authentication successful."
        );

        if (result.redirect_url) {

            window.location.href =
                result.redirect_url;

        } else {

            window.location.href = "/";
        }

    } catch (error) {

        console.error(
         "Passkey authentication failed:",
        error
        );

        alert(
            "Passkey authentication failed:\n\n" +
            error.name +
            "\n" +
             error.message
            );

        throw error;
    }
}
