// snippet_id: http-handler-basic
// description: Basic HTTP handler that returns JSON
// features: [http, json-response]
// complexity: beginner

package main

import (
    "net/http"
    "github.com/transire/transire-sdk-go/response"
)

func handler(w http.ResponseWriter, r *http.Request) {
    response.OK(w, map[string]string{
        "message": "Success",
    })
}
