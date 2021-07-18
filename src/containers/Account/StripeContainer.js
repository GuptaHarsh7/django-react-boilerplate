import React from 'react';
import './App.css';
import {
  Elements,
} from '@stripe/react-stripe-js';

import {loadStripe} from "@stripe/stripe-js/pure";
import SubscribeForm from "./SubscribeForm";

const stripePromise = loadStripe('pk_test_51Ix7DoSDH8LbnqpkFoCtxoUTlK5GVbOIoy6UP3X8IjrACXjbJZ9NsRycNOIXQVkWKvGpWaNYp5gbSZ1rNdjJJa8F00tcZVdh3E');


const StripeContainer = () => (
    <Elements stripe={stripePromise}>
      <SubscribeForm />
    </Elements>
);

export default StripeContainer;