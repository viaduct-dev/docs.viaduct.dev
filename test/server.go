package main

import (
	"net/http"
	"os"
)

func main() {
	if len(os.Args) > 1 && os.Args[1] == "--health" {
		resp, err := http.Get("http://localhost:8080/")
		if err != nil || resp.StatusCode != 200 {
			os.Exit(1)
		}
		return
	}
	if err := http.ListenAndServe(":8080", http.FileServer(http.Dir("/srv"))); err != nil {
		os.Exit(1)
	}
}
