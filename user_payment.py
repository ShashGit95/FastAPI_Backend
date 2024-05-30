from fastapi import HTTPException, Request
import json
import os
import stripe



# Configure Stripe
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
webhook_secret = os.environ["STRIPE_WEBHOOK_SECRET"]


# starting payment intent
async def payment_intent():

    try:
        # Set the amount and currency directly, bypassing the need to extract from request
        amount = 9900  # Amount in cents for $99
        currency = 'usd'  # Currency set to USD

        # validating amount and currency if they are not pre determined. 
        if amount is None or not isinstance(amount, int) or amount <= 0:
            raise ValueError("Invalid amount. Must be a positive integer representing cents.")

        
        if currency not in ['usd', 'eur', 'gbp']:  # Extend this list based on the currencies you support
            raise ValueError("Unsupported currency.")

        # Call the function to create a Payment Intent
        payment_intent = await create_payment_intent_backend(amount, currency)
        return payment_intent
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Consider logging the exception details here for debugging
        raise HTTPException(status_code=500, detail="An error occurred while processing the payment intent.")


# Function to create a Payment Intent with specific payment methods
async def create_payment_intent_backend(amount: int, currency: str):

    try:
        # Define the payment methods you want to accept
        payment_method_types = ['card']  # You can add more methods here, e.g., ['card', 'bank_transfer']

        # Create a Payment Intent with the specified amount, currency, and payment methods
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,  # Amount is in cents
            currency=currency,
            payment_method_types=payment_method_types,
            # Add any other parameters you need here, e.g., customer
        )
        # Return the client secret and any other information your frontend may need
        return {"clientSecret": payment_intent.client_secret}
    
    except stripe.error.StripeError as e:
        # Handle any errors from Stripe
        raise e


# use webhooks to receive information about asynchronous payment events.
async def webhook_received(request: Request):
    
    request_data = await request.body()

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload=request_data, sig_header=signature, secret=webhook_secret
            )
            data = event["data"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event["type"]
    else:
        request_json = json.loads(request_data)
        data = request_json["data"]
        event_type = request_json["type"]

    data_object = data["object"]

    # Handling the payment_intent.created event
    if event_type == "payment_intent.created":
        payment_intent = event['data']['object']
        print('🔔 [%s] PaymentIntent(%s): (%s)' % (event.id, payment_intent.id, payment_intent.status ))
        # Here you can add logic to handle the payment intent creation,
        # such as logging the event or updating your application's state.
        

    elif event_type == "payment_intent.succeeded":
        payment_intent = event['data']['object']
        print('💰 [%s] PaymentIntent(%s): (%s)' % (event.id, payment_intent.id, payment_intent.status ))
        # Fulfill any orders, e-mail receipts, etc
        # To cancel the payment you will need to issue a Refund (https://stripe.com/docs/api/refunds)

        
    elif event_type == "payment_intent.payment_failed":
        payment_intent = event['data']['object']
        print('❌ [%s] PaymentIntent(%s): (%s)' % (event.id, payment_intent.id, payment_intent.status ))
        # Here you could notify the customer, initiate a retry, or log for review.
    
         
    elif event_type == "payment_intent.processing":
        payment_intent = event['data']['object']
        print('🔔 [%s] PaymentIntent(%s): (%s)' % (event.id, payment_intent.id, payment_intent.status ))


    # Handling the payment_intent.canceled event
    elif event_type == "payment_intent.canceled":
        payment_intent = event['data']['object']
        print('❌ [%s] PaymentIntent(%s): (%s)' % (event.id, payment_intent.id, payment_intent.status ))
        # Similar to creation, handle cancellations by updating your system accordingly.

    else:
        print(f"Unhandled event type: {event_type}")

    return {"status": "success"}




# # checkout function -payment  powered by stripe
# async def checkout_session(request, stripe_customer_id):

#     data = await request.json()

#     if not stripe_customer_id:
#         customer = stripe.Customer.create(
#             description="Demo customer",
#         )
#         stripe_customer_id = customer["id"]

#     checkout_session = stripe.checkout.Session.create(
#         customer=stripe_customer_id,
#         success_url="http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}",
#         cancel_url="http://localhost:8000/cancel",
#         payment_method_types=["card"],
#         mode="subscription",
#         line_items=[{
#             "price": data["priceId"],
#             "quantity": 1
#         }],
#     )
#     return {"sessionId": checkout_session["id"]}
    


# # portal session function -payment gateway powered by stripe
# async def portal_session(stripe_customer_id):
   
#    session = stripe.billing_portal.Session.create(
#         customer=stripe_customer_id,
#         return_url="http://localhost:8000"
#     )
#    return {"url": session.url}



# # create webhook function -payment gateway powered by stripe
# async def create_webhook(request, stripe_signature, webhook_secret):
#     data = await request.body()
#     try:
#         event = stripe.Webhook.construct_event(
#             payload=data,
#             sig_header=stripe_signature,
#             secret=webhook_secret
#         )
#         event_data = event['data']
#     except Exception as e:
#         return {"error": str(e)}

#     event_type = event['type']

#     if event_type == 'payment_intent.created':
#         print(' Payment Intent Created.')
#     # if event_type == 'checkout.session.completed':
#     #     print('checkout session completed')
#     # elif event_type == 'invoice.paid':
#     #     print('invoice paid')
#     # elif event_type == 'invoice.payment_failed':
#     #     print('invoice payment failed')
#     else:
#         print(f'unhandled event: {event_type}')
    
#     return {"status": "success"}



