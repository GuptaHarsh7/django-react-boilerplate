from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from .serializers import *
from rest_framework.decorators import api_view
import stripe
from .models import TrackedRequest, Payment
from rest_framework import status
from .models import *
from .image_detection import detect_faces
from .permissions import IsMember
import datetime
import math

User = get_user_model()
STRIPE_PLAN_ID = "prod_Jf80HiMo9qf5nD"


class FileUplaodView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):

        content_length = request.META.get('CONTENT_LENGTH')

        if int(content_length) > 5000000:
            return Response({"message": "Image size is greater than 5MB"}, status=HTTP_400_BAD_REQUEST)

        file_serializer = FileSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save()
            image_path = file_serializer.data.get('file')
            recognition = detect_faces(image_path)
            print(recognition)
        return Response(recognition, status=HTTP_200_OK)


def get_user_from_token(request):
    key = request.META.get("HTTP_AUTHORIZATION").split(' ')[1]
    token = Token.objects.get(key=key)
    user = User.objects.get(id=token.user_id)
    return user


class ChangeEmailView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        email_serializer = ChangeEmailSerializers(data=request.data)
        if email_serializer.is_valid():
            email = email_serializer.data.get('email')
            confirm_email = email_serializer.data.get('confirm_email')
            if email == confirm_email:
                user.email = email
                user.save()

                return Response({
                    "email": email,
                }, status=HTTP_200_OK)

            return Response({
                "message": "The emails do not match",
            }, status=HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Incorrect DATA",
        }, status=HTTP_400_BAD_REQUEST)


class EmailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        obj = {'email': user.email}
        return Response(obj)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        password_serializer = ChangePasswordSerializers(data=request.data)
        if password_serializer.is_valid():
            password = password_serializer.data.get('password')
            confirm_password = password_serializer.data.get('confirm_password')
            current_password = password_serializer.data.get('current_password')

            auth_user = authenticate(
                username=user.username,
                password=current_password
            )

            if auth_user is not None:
                if password == confirm_password:
                    auth_user.set_password(password)
                    auth_user.save()
                    return Response(status=HTTP_200_OK)
                return Response({
                    "message": "The passwords do not match",
                }, status=HTTP_400_BAD_REQUEST)
            return Response({
                "message": "Incorrect User Details",
            }, status=HTTP_400_BAD_REQUEST)
        return Response({
            "message": "Incorrect DATA",
        }, status=HTTP_400_BAD_REQUEST)


class UserDetailsView(APIView):

    def get(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        membership = user.membership
        today = datetime.datetime.now()
        month_start = datetime.date(today.year, today.month, 1)
        tracked_request_count = TrackedRequest.objects.filter(
            user=user, timestamp__gte=month_start).count()
        amount_due = 0

        # usage_record = stripe.SubscriptionItem.create_usage_record(
        #     membership.stripe_subscription_item_id, quantity=tracked_request_count, timestamp=math.floor(datetime.datetime.now().timestamp()),)
        # print(usage_record)
        if user.is_member:
            amount_due = stripe.Invoice.upcoming(
                customer=user.stripe_customer_id)['amount_due'] / 100
        obj = {
            'membershipType': membership.get_type_display(),
            'free_trial_end_date': membership.end_date,
            'next_billing_date': membership.end_date,
            'api_request_count': tracked_request_count,
            'amount_due': amount_due
        }
        return Response(obj)


# Create your views here.
stripe.api_key = "sk_test_51Ix7DoSDH8LbnqpkT3MyKegLDXZWeBvwsCdrX5HyLpcbLxWfxCBRkA0TF1JUb1kezcDIHc26TC7DLQhpk9yQPudT00zZIB8J8w"


class SubscribeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = get_user_from_token(request)

        # get the user membership
        membership = user.membership

        try:
            # get the stripe customer
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            serializer = SubscribeSerializer(data=request.data)

            # serialize post data (stripeToken)
            if serializer.is_valid():
                # get stripeTOken from serializer data
                stripe_token = serializer.data.get('stripeToken')

                # create the stripe subscription

                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{"plan": STRIPE_PLAN_ID}]
                )

                # update the membership
                membership.stripe_subscription_id = subscription.id
                membership.type = "M"
                membership.start_date = datetime.dateime.now()
                membership.stripe_subscription_item_id = subscription['items']['data'][0]['id']
                membership.end_date = datetime.datetime.fromtimestamp(
                    subscription.current_period_end)
                membership.save()

                # update the user
                user.is_member = True
                user.on_free_trial = False
                user.save()

                # create payment
                payment = Payment()
                payment.amount = subscription.plan.amount
                payment.user = user
                payment.save()
                return Response({"message": "SUCCESS"}, status=HTTP_200_OK)

            else:
                return Response({"message": "Incorrect data was received"}, status=HTTP_400_BAD_REQUEST)

        except stripe.error.CardError as e:
            return Response({"message": "Your card has been declined"}, status=HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            return Response({"message": "There was an error. You have not been billed. If this persists please contact support"}, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "We apologize for the error. We have been informed and are working on the issue. "}, status=HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def test_payment(request):
#     test_payment_intent = stripe.PaymentIntent.create(
#         amount=1000,
#         currency='pln',
#         description='Software development services',
#         shipping={
#             'name': 'Jenny Rosen',
#             'address': {
#                 'line1': '510 Townsend St',
#                 'postal_code': '98140',
#                 'city': 'San Francisco',
#                 'state': 'CA',
#                 'country': 'US',
#             },
#         },
#         payment_method_types=['card'],
#         receipt_email='test@example.com',
#     )

#     return Response(status=status.HTTP_200_OK, data=test_payment_intent)


@api_view(['POST'])
def confirm_payment_intent(request):
    data = request.data
    payment_intent_id = data['payment_intent_id']

    stripe.PaymentIntent.confirm(payment_intent_id)

    return Response(status=status.HTTP_200_OK, data={"message": "Success"})


@api_view(['POST'])
def save_stripe_info(request):

    user = User.objects.get(email=request.data['email'])
    membership = user.membership
    name = user.get_full_name()
    print(name)
    address = user.address

    data = request.data
    email = data['email']
    payment_method_id = data['payment_method_id']
    extra_msg = ''
    # checking if customer with provided email already exists
    customer_data = stripe.Customer.list(email=email).data
    print(customer_data)

    if len(customer_data) == 0:
        # creating customer
        customer = stripe.Customer.create(
            email=email,
            name=name,
            address={
                'line1': address.line1,
                'postal_code': address.postal_code,
                'city': address.city,
                'state': 'CA',
                'country': 'US',
            },
            payment_method=payment_method_id,
            invoice_settings={
                'default_payment_method': payment_method_id
            }
        )
        user.stripe_customer_id = customer.id
    else:
        customer = customer_data[0]
        extra_msg = "Customer already existed."

    ItemSubscription = stripe.Price.retrieve("price_1J4r3bSDH8Lbnqpk7OAubG1T")
    amount = ItemSubscription["unit_amount"]

    # creating paymentIntent

    stripe.PaymentIntent.create(customer=customer,
                                description='Software development services',
                                shipping={
                                    'name': name,
                                    'address': {
                                        'line1': address.line1,
                                        'postal_code': address.postal_code,
                                        'city': address.city,
                                        'state': 'CA',
                                        'country': 'US',
                                    },
                                },
                                payment_method=payment_method_id,
                                currency='usd', amount=amount,
                                confirm=True)

    # creating subscription

    subscription = stripe.Subscription.create(
        customer=customer,
        items=[
            {
                'price': 'price_1J4r3bSDH8Lbnqpk7OAubG1T'
            }
        ]
    )

# update the membership
    membership.stripe_subscription_id = subscription.id
    membership.type = "M"
    membership.start_date = datetime.datetime.now()
    membership.stripe_subscription_item_id = subscription["items"]["data"][0]["id"]
    membership.end_date = datetime.date.fromtimestamp(
        subscription.current_period_end)
    membership.save()

    # update the user
    user.is_member = True
    user.on_free_trial = False
    user.save()

    return Response(status=status.HTTP_200_OK, data={'message': 'Success', 'data': {'customer_id': customer.id,
                                                                                    'extra_msg': extra_msg}})


class ImageRecognitionView(APIView):
    permission_classes = (IsMember,)

    def post(self, request, *args, **kwargs):

        user = get_user_from_token(request)
        membership = user.membership
        file_serializer = FileSerializer(data=request.data)

        usage_record_id = None

        # if user.is_member:
        # usage_record = stripe.UsageRecord.create(
        #     quantity=1, timestamp=math.floor(datetime.datetime.now().timestamp()), subscription_item=membership.stripe_subscription_item_id
        # )
        # usage_record = stripe.SubscriptionItem.create_usage_record(
        #     membership.stripe_subscription_item_id, quantity=1, timestamp=math.floor(datetime.datetime.now().timestamp()),)
        # usage_record_id = usage_record.id

        tracked_request = TrackedRequest()
        tracked_request.user = user
        # tracked_request.usage_record_id = usage_record_id
        tracked_request.endpoint = '/api/image-recognition/'
        tracked_request.save()

        content_length = request.META.get('CONTENT_LENGTH')

        if int(content_length) > 5000000:
            return Response({"message": "Image size is greater than 5MB"}, status=HTTP_400_BAD_REQUEST)

        if file_serializer.is_valid():
            file_serializer.save()
            image_path = file_serializer.data.get('file')
            recognition = detect_faces(image_path)
            print(recognition)
            return Response(recognition, status=HTTP_200_OK)
        return Response({"Received Incorrect data"}, status=HTTP_400_BAD_REQUEST)


class APIKeyView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        token_qs = Token.objects.filter(user=user)

        if token_qs.exists():
            token_serializer = TokenSerializer(token_qs, many=True)
            try:
                return Response(token_serializer.data, status=HTTP_200_OK)
            except Exception:
                return Response({"message": "Did not receive correct data"}, status=HTTP_400_BAD_REQUEST)
        return Response({"message": "User does not exist"}, status=HTTP_400_BAD_REQUEST)


class CancelSubscription(APIView):
    permission_classes = (IsMember, )

    def post(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        membership = user.membership

        try:
            stripe.Subscription.delete(membership.stripe_subscription_id)

            user.is_member = False
            user.save()

            membership.type = "N"
            membership.save()
        except Exception as e:
            return Response({"message": "We apologize for the error. We have been informed and are working on the issue. "}, status=HTTP_400_BAD_REQUEST)

        return Response({"message": "Your Subscription was cancelled."}, status=HTTP_200_OK)
