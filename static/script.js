var createCheckoutSession = function(priceId) {
    return fetch("/create-checkout-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        priceId: priceId
      })
    }).then(function(result) {
      return result.json();
    });
  };

const PREMIUM_PRICE_ID = "";
const BASIC_PRICE_ID = "price_1OrLPFJFP82GiCWfuCDa9PTg";
const stripe = Stripe("pk_test_51Or2igJFP82GiCWf8T9rsLEE9BWvhAFfxaFcsxJqmL9SFbFtLM4jgo97AOrpsyd033qZIFgGUtN6EjN6XFZMr2CW00BXHtLNtq");

document.addEventListener("DOMContentLoaded", function(event) {
    // document
    // .getElementById("checkout-premium")
    // .addEventListener("click", function(evt) {
    //     createCheckoutSession(PREMIUM_PRICE_ID).then(function(data) {
    //         stripe
    //             .redirectToCheckout({
    //                 sessionId: data.sessionId
    //             });
    //         });
    //     });
    
    document
    .getElementById("checkout-basic")
    .addEventListener("click", function(evt) {
        createCheckoutSession(BASIC_PRICE_ID).then(function(data) {
            stripe
                .redirectToCheckout({
                    sessionId: data.sessionId
                });
            });
        });

    const billingButton = document.getElementById("manage-billing");
    if (billingButton) {
        billingButton.addEventListener("click", function(evt) {
        fetch("/create-portal-session", {
            method: "POST"
        })
            .then(function(response) {
                return response.json()
            })
            .then(function(data) {
                window.location.href = data.url;
            });
        })
    }
});