package com.example;

import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

public class SimpleGetRequest {

    public static void main(String[] args) {
        // Define the API endpoint
        String url = "https://jsonplaceholder.typicode.com/posts/1"; // Replace with your API endpoint

        // Create a RestTemplate instance
        RestTemplate restTemplate = new RestTemplate();

        // Send the GET request
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

            // Check if the request was successful
            if (response.getStatusCode().is2xxSuccessful()) {
                // Print the response body
                System.out.println("Response Body:");
                System.out.println(response.getBody());
            } else {
                System.out.println("Request failed with status code: " + response.getStatusCode());
            }
        } catch (Exception e) {
            System.out.println("An error occurred: " + e.getMessage());
        }
    }
}
